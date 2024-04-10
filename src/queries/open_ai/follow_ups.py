import asyncio
import logging
import sys
from typing import Any, List, Tuple

from openai import AsyncOpenAI, OpenAI
from psycopg2.extensions import connection
from pydantic import BaseModel, Field

from data_models.appointment_summary import FollowUps
from db import CREATE_QUERIES, create_connection, query_db
from queries.open_ai.appointments import OAIRequest, a_send_rqt, send_rqt

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

Please add filter the sql query to only return providers that are in the 
same location as the patient and accept the same insurance as the patient.
The patients location is = {} and the patients insurance id is = {}.

For insurance id, you can structure your query like the following:
AND providers.id in (
                    select provider_id from provider_to_insurance pti 
		            where pti.insurance_id = "patient_insurance_id"

If insurance_id or location are empty strings, do not include the filter for them in the query. 

"""


def get_location_and_insurance(conn, user_id: int) -> str:
    get_info = f"SELECT u.location, u.insurance_id FROM users u WHERE u.id = {user_id}"
    result = query_db(conn, get_info)
    logging.info(f"Result from filter statement: {result}")

    if not result:
        return "", ""  # is this the behavior we want?

    location = result[0][0]
    insurance_id = result[0][1]

    return location, insurance_id


async def get_followup_suggestions(
    client: OpenAI | AsyncOpenAI, conn: connection, user_id: int, tasks: FollowUps
) -> list[Any]:
    """Get follow up suggestions for the patient based on the tasks assigned by the physician."""

    location, insurance_id = get_location_and_insurance(conn, user_id)
    rqt = OAIRequest(
        system_msg=SYSTEM_MSG.format(FollowUpQueries.model_json_schema()),
        user_msg=USER_MSG.format(tasks, location, insurance_id),
        response_schema=FollowUpQueries,
        tools=TOOLS,
        tool_choices=TOOL_CHOICE,
    )

    response = await a_send_rqt(client, rqt)
    logging.info(f"Response for SQL Query: {response}")

    followup_suggestions = []
    for task in response.tasks:
        logging.info(f"Query for Task: {task.query}")
        result = query_db(conn, task.query)
        logging.info(f"Result: {result}")

        followup_suggestions.append(result)

    return followup_suggestions


if __name__ == "__main__":
    tasks = {
        "tasks": [
            {"task": "Consult Allergy and GI."},
            {"task": "AMB REF TO ALLERGY & CLIN IMM (FPA ASTHMA)."},
            {"task": "AMB REF TO GASTROENTEROLOGY."},
        ]
    }
    client = AsyncOpenAI()
    conn = create_connection()
    user_id = 1

    async def main():
        followup_suggestions = await get_followup_suggestions(
            client, conn, user_id, tasks
        )
        await client.close()

    asyncio.run(main())
    conn.close()
