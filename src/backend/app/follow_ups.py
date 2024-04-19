import asyncio
import logging
import sys
from typing import Any, List, Tuple

from openai import AsyncOpenAI, OpenAI
from psycopg2.extensions import connection
from pydantic import BaseModel, Field

from ..db.relational_db import CREATE_QUERIES, create_connection, query_db
from ..models.open_ai.utils import OAIRequest, a_send_rqt
from .appointments import FollowUps, SpecialtyEnum, specialties

logger = logging.getLogger(__name__)

print(specialties)


class TaskSpecialty(BaseModel):
    """A model to represent the correct specialty to book with given an associated follow up tasks"""

    specialty: SpecialtyEnum | None = Field(  # type: ignore
        default=None, description="""The specialty of the provider"""
    )


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
                                - specialties.specialty: 'ENT', 'ALLERGIST', 'GASTRO', 'CARDIO', 'DERM', 'NEURO', 'ORTHO', 'SPORTS', 'SLEEP'
                                
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

# SYSTEM_MSG = """You are an expert SQL practioners specialized in medical data.
# A physician has assigned follow up tasks for the patient. Your job is to translate
# these tasks into a SQL query to help identify suitable doctors for the follow up tasks.
# If the multiple tasks provided are related, you can write a single query that will help identify suitable doctors for all the tasks.
# Follow the JSON schema provided below to ensure the information is returned in the correct format.
# JSON Schema:
# {}
# """
# USER_MSG = """The physician has assigned the following follow up task for the patient:
# {}
# Please write a SQL query that will help identify suitable doctors for this follow up task.
# For example, if the task was 'Schedule an appointment with a ENT specialist.',
# you could write a query that would return a list of ENT specialists using the database schema.

# Please filter the sql query to only return providers that are in the
# same city as the patient and accept the same insurance as the patient.
# The patients city is = {} and the patients insurance id is = {}.

# For insurance id, you can structure your query like the following:
# AND providers.id in (
#                     select provider_id from provider_to_insurance pti
# 		            where pti.insurance_id = "patient_insurance_id"

# If insurance_id or location are empty strings, do not include the filter for them in the query.

# """

SYSTEM_MSG = """
You are an expert medical assistant and are helping us match physician follow up tasks
to the right type of specialty. You will be provided with follow up tasks by a doctor e.g. 
"Consult an ENT". You will also be provided a list of physician specialties such as ORTHO and ENT. 
For each task, your job is to match the etask with a specialty provided a list of specialties. 
Continuing the ENT example, if the list of specialties was presented was [ENT, ORTHO, SPORTS MEDICINE]
you would return ENT. 

Please only return your format in JSON schema using the JSON schema below. 
JSON Schema: 
{}

If you are unsure, please return None. 
"""

USER_MSG = """The physician has assigned the following follow up task for the patient:
{}
For each task please associate the follow up tasks with one of the following physician specialties 
{}

As an example, if the task is 'consult sports medicine for back' then you would choose SPORTS.  
"""


def get_location_and_insurance(conn, user_id: int) -> str:
    get_info = f"SELECT u.location, u.insurance_id FROM users u WHERE u.id = {user_id}"
    result = query_db(conn, get_info)
    logger.info(f"Result from filter statement: {result}")

    if not result:
        return "", ""  # is this the behavior we want?

    location = result[0][0]
    insurance_id = result[0][1]

    return location, insurance_id


async def get_followup_suggestions(
    client: OpenAI | AsyncOpenAI, conn: connection, user_id: int, tasks: FollowUps
) -> list[Any]:
    """Get follow up suggestions for the patient based on the tasks assigned by the physician."""
    # location, insurance_id = get_location_and_insurance(conn, user_id)
    followup_suggestions = []
    for task in tasks:
        logger.info(f"Receiving query for follow up task: {task}")
        rqt = OAIRequest(
            system_msg=SYSTEM_MSG.format(TaskSpecialty.model_json_schema()),
            user_msg=USER_MSG.format(task, ", ".join(specialties.keys())),
            response_schema=TaskSpecialty,
            # tools=TOOLS,
            # tool_choices=TOOL_CHOICE,
        )

        response = await a_send_rqt(client, rqt)
        print(f"Task: {task}, Response: {response}")
        # logger.info(f"Query for Task: {response.query}\n")
        # result = query_db(conn, response.query)
        # logger.info(f"Result: {result}\n")
        # followup_suggestions.append({"task": task, "result": result})

    return followup_suggestions


if __name__ == "__main__":
    tasks = [
        {"task": "Referral to ENT specialist for chronic cough."},
        {"task": "Consider sleep study for persistent insomnia issues."},
        {"task": "Referral to sports medicine for full evaluation of lower back pain."},
    ]
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
