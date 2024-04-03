import logging
import sys
from typing import List

from openai import OpenAI
from pydantic import BaseModel, Field

from src.db import (
    CREATE_INSURANCE_QUERY,
    CREATE_PROVIDER_QUERY,
    CREATE_PROVIDER_TO_INSURANCE_QUERY,
    CREATE_QUERIES,
    CREATE_SPECIALTIES_QUERY,
    CREATE_USER_QUERY,
    CREATE_USER_TO_INSURANCE_QUERY,
    create_connection,
    query_db,
)
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


# database_schema_string = "\n".join(
#     [
#         CREATE_PROVIDER_QUERY,
#         CREATE_USER_QUERY,
#         CREATE_INSURANCE_QUERY,
#         CREATE_PROVIDER_TO_INSURANCE_QUERY,
#         CREATE_USER_TO_INSURANCE_QUERY,
#         CREATE_SPECIALTIES_QUERY,
#     ]
# )

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


# TODO: add where statement to filter for location and insurance of patient

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
    for task in response.tasks:
        logging.info(f"Query for Task: {task.query}")

        assert isinstance(task.query, str)
        result = query_db(conn, task.query)

        logging.info(f"Result: {result}")

    conn.close()
    client.close()
