import logging
import sys
from typing import Any, List, Tuple

from openai import AsyncOpenAI, OpenAI
from pydantic import BaseModel, Field

from src.data_models.appointment_summary import FollowUps
from src.db import CREATE_QUERIES, create_connection, query_db
from src.queries.open_ai.appointments import OAIRequest, a_send_rqt, send_rqt

logging.basicConfig(stream=sys.stdout, level=logging.INFO)


class TaskQuery(BaseModel):
    """A model to represent the database query to run to extract information that will help with the follow up tasks assigned"""

    query: str = Field(
        ..., description="SQL query extracting info to assist in follow up tasks."
    )


class FollowUpQueries(BaseModel):
    """A model to represent the follow up tasks assigned to the patient"""

    tasks: List[TaskQuery] = Field(..., description="A query for each follow up task")


database_schema_string = "\n".join(CREATE_QUERIES)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "ask_database",
            "description": "Use this function to look for suitable doctors for the follow up tasks. Input should be a fully formed SQL query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": f"""
                                SQL query extracting info to assist in follow up tasks.
                                SQL should be written using this database schema:
                                {database_schema_string}
                                The following columns only contain the following values:
                                - specialties.specialty: 'ENT', 'ALLERGIST', 'GASTRO'
                                
                                The query should be returned in plain text, not in JSON.
                                """,
                    }
                },
                "required": ["query"],
            },
        },
    }
]

TOOL_CHOICE = {"type": "function", "function": {"name": "ask_database"}}

SYSTEM_MSG = """You are an expert SQL practioners specialized in medical data.
A physician has assigned follow up tasks for the patient. Your job is to translate
these tasks into a SQL query to help identify suitable doctors for the follow up tasks.
If the multiple tasks provided are related, you can write a single query that will help identify suitable doctors for all the tasks.
Follow the JSON schema provided below to ensure the information is returned in the correct format.
JSON Schema: 
{}
"""
USER_MSG = """The physician has assigned the following follow up tasks for the patient:
{}
Please write a SQL query that will help identify suitable doctors for these follow up tasks.
For example, if the task was 'Schedule an appointment with a ENT specialist.', 
you could write a query that would return a list of ENT specialists using the database schema. 
"""


def create_filter_statement(conn, user_id: int) -> str:
    get_info = f"SELECT u.location, u.insurance_id FROM users u WHERE u.id = {user_id}"
    result = query_db(conn, get_info)
    logging.info(f"Result: {result}")

    if not result:
        return ""  # is this the behavior we want?

    location = result[0][0]
    insurance_id = result[0][1]

    return f"""AND providers.location = '{location}' 
               AND providers.id in (
                    select provider_id from provider_to_insurance pti 
		            where pti.insurance_id = {insurance_id}
               )"""


async def get_followup_suggestions(
    client: OpenAI | AsyncOpenAI, user_id: int, tasks: FollowUps
) -> list[Any]:
    """Get follow up suggestions for the patient based on the tasks assigned by the physician."""
    rqt = OAIRequest(
        system_msg=SYSTEM_MSG.format(FollowUpQueries.model_json_schema()),
        user_msg=USER_MSG.format(tasks),
        response_schema=FollowUpQueries,
        tools=TOOLS,
        tool_choices=TOOL_CHOICE,
    )
    conn = create_connection()
    filter_statement = create_filter_statement(conn, user_id)
    response = await a_send_rqt(client, rqt)

    logging.info(f"Response: {response}")

    followup_suggestions = []
    for task in response.tasks:
        query = task.query + filter_statement
        logging.info(f"Query for Task: {query}")

        result = query_db(conn, query)
        logging.info(f"Result: {result}")

        followup_suggestions.append(result)

    conn.close()
    return followup_suggestions


if __name__ == "__main__":
    tasks = {
        "tasks": [
            {"task": "Consult Allergy and GI."},
            {"task": "AMB REF TO ALLERGY & CLIN IMM (FPA ASTHMA)."},
            {"task": "AMB REF TO GASTROENTEROLOGY."},
        ]
    }
    rqt = OAIRequest(
        system_msg=SYSTEM_MSG.format(FollowUpQueries.model_json_schema()),
        user_msg=USER_MSG.format(tasks),
        response_schema=FollowUpQueries,
        tools=TOOLS,
        tool_choices=TOOL_CHOICE,
    )

    client = OpenAI()
    conn = create_connection()
    user_id = 1
    # this will need to be added dynamically

    filter_statement = create_filter_statement(conn, user_id)
    response = send_rqt(client, rqt)

    logging.info(f"Response: {response}")

    for task in response.tasks:
        query = task.query + filter_statement
        logging.info(f"Query for Task: {query}")

        result = query_db(conn, query)
        logging.info(f"Result: {result}")

    conn.close()
    client.close()
