import logging
import sys
from typing import List

from openai import OpenAI
from pydantic import BaseModel, Field

from src.db import CREATE_QUERIES, create_connection, query_db
from src.queries.open_ai.appointments import OAIRequest, send_rqt

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))


class TaskQuery(BaseModel):
    """A model to represent the database query to run to extract information that will help with the follow up tasks assigned"""

    query: str = Field(
        ..., description="SQL query extracting info to assist in follow up tasks."
    )


class FollowUpQueries(BaseModel):
    """A model to represent the follow up tasks assigned to the patient"""

    tasks: List[TaskQuery] = Field(..., description="A query for each follow up task")


database_schema_string = "\n".join(CREATE_QUERIES)

tools = [
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


tasks = {
    "tasks": [
        {"task": "Consult Allergy and GI."},
        {"task": "AMB REF TO ALLERGY & CLIN IMM (FPA ASTHMA)."},
        {"task": "AMB REF TO GASTROENTEROLOGY."},
    ]
}

tool_choice = {"type": "function", "function": {"name": "ask_database"}}


# TODO: add where statement to filter for location and insurance of patient, and need ranking criteria


def create_filter_statement(user_info: dict[str]) -> str:
    return f"WHERE location = '{user_info['location']}' AND insurance = '{user_info['insurance']}'"


rqt = OAIRequest(
    system_msg=SYSTEM_MSG.format(FollowUpQueries.model_json_schema()),
    user_msg=USER_MSG.format(tasks),
    response_schema=FollowUpQueries,
    tools=tools,
    tool_choices=tool_choice,
)

if __name__ == "__main__":
    client = OpenAI()
    conn = create_connection()

    response = send_rqt(client, rqt)
    logging.info(f"Result with filter: {response}")

    for task in response.tasks:
        query = task.query + create_filter_statement(response.user_info)
        logging.info(f"Query for Task: {query}")
        result = query_db(conn, query)
        logging.info(f"Result: {result}")

    conn.close()
    client.close()
