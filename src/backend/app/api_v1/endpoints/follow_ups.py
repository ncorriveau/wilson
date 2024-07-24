import asyncio
import logging
import os
from pprint import pprint
from typing import Any, Dict

from fastapi import APIRouter, Depends
from openai import AsyncOpenAI, OpenAI
from psycopg2.extensions import connection
from pydantic import BaseModel, Field
from pymongo import MongoClient
from pymongo.collection import Collection

from ...db.nosql_db import get_relevant_providers
from ...deps import get_current_user
from ...models.open_ai.utils import OAIRequest, a_send_rqt
from ...pydantic_models.pyd_models import FollowUpRqt, TaskSpecialty, specialties
from .appointments import FollowUps

logger = logging.getLogger(__name__)

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")

SYSTEM_MSG = """
You are an expert medical assistant and are helping us match physician follow up tasks
to the right type of specialty. You will be provided with follow up tasks by a doctor e.g. 
"Consult an ENT". You will also be provided a list of physician specialties such as ORTHO and ENT. 
For each task, your job is to match the task with a specialty provided a list of specialties. 
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


async def get_followup_suggestions(
    client: OpenAI | AsyncOpenAI,
    collection: Collection,
    patient_info: Dict[str, Any],
    tasks: FollowUps,
) -> list[Any]:
    """
    Get follow up suggestions for the patient based on the tasks assigned
    by the physician and the location of the user.

    Parameters
    ----------
    client : OpenAI | AsyncOpenAI
        The OpenAI client to send requests to
    conn : connection | Collection
        The connection to the database
    patient_info : Dict[str, Any]
        The information about the patient including the location and insurance_id
        of the user
    """
    followup_suggestions = []
    for task in tasks:
        logger.info(f"Receiving query for follow up task: {task}")
        rqt = OAIRequest(
            system_msg=SYSTEM_MSG.format(TaskSpecialty.model_json_schema()),
            user_msg=USER_MSG.format(task, ", ".join(specialties.keys())),
            response_schema=TaskSpecialty,
        )

        response = await a_send_rqt(client, rqt)
        logger.info(f"Task: {task}, Response: {response}")
        result = get_relevant_providers(
            collection, patient_info, response.specialty.value
        )

        # TODO: clean this up this is ugly
        # we are deleting because _id is not serializable
        if result:
            del result[0]["_id"]

        logger.info(f"Result: {pprint(result)}\n")
        followup_suggestions.append({"provider": result, "task": task})

    return followup_suggestions


router = APIRouter(dependencies=[Depends(get_current_user)])
client = AsyncOpenAI()
mongo_db_client = MongoClient(MONGODB_URL)
db = mongo_db_client["wilson_ai"]
provider_collection = db.providers


@router.post("/")
async def get_follow_ups(followup_rqt: FollowUpRqt):
    tasks = followup_rqt.follow_ups.tasks
    logging.info(f"Received tasks: {tasks}")
    follow_ups = await get_followup_suggestions(
        client, provider_collection, followup_rqt.user_info.model_dump(), tasks
    )
    return follow_ups


if __name__ == "__main__":
    client = AsyncOpenAI()
    client_db = MongoClient(MONGODB_URL)
    db = client_db["wilson_ai"]
    collection = db.providers

    tasks = [
        {"task": "Schedule with Primary Care Physician."},
        # {"task": "Consider sleep study for persistent insomnia issues."},
        # {"task": "Referral to sports medicine for full evaluation of lower back pain."},
    ]
    user_loc = {"lat": 40.7197743, "lng": -73.9641896, "insurance_id": 3}

    async def main():
        followup_suggestions = await get_followup_suggestions(
            client, collection, user_loc, tasks
        )
        print(followup_suggestions)
        await client.close()

    asyncio.run(main())
