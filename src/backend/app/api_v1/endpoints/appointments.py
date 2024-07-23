import json
import logging
import os
import time
from pprint import pprint
from typing import Type
from uuid import uuid4

import aioredis
import boto3
from dotenv import load_dotenv
from fastapi import APIRouter, BackgroundTasks, File, Header, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from llama_index.core import SimpleDirectoryReader, download_loader
from openai import AsyncOpenAI, OpenAI
from psycopg2.extensions import connection
from pydantic import BaseModel, Field
from pymongo import MongoClient

from ...db.nosql_db import get_provider_by_npi, get_provider_id, upsert_provider
from ...db.relational_db import (
    create_connection,
    get_user_appointments,
    upsert_appointment,
    upsert_prescription,
)
from ...db.vector_db import load_documents
from ...deps import get_current_user
from ...models.open_ai import prompts as oai_prompts
from ...models.open_ai.utils import OAIRequest, a_send_rqt
from ...pydantic_models.pyd_models import (
    AppointmentMeta,
    ApptRqt,
    FollowUps,
    Perscriptions,
    Summary,
    specialties,
)
from ...utils.utils import create_hash_id, get_locations

load_dotenv()

logger = logging.getLogger(__name__)

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost")
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")

METADATA_PARAMS = [
    "user_id",
    "provider_id",
    "filename",
    "appointment_date",
]
locations = get_locations()
client = AsyncOpenAI()
redis = aioredis.from_url(REDIS_URL)
mongo_db_client = MongoClient(MONGODB_URL)

db = mongo_db_client["wilson_ai"]
provider_collection = db.providers
conn = create_connection()

s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)
S3Reader = download_loader("S3Reader")


class AppointmentAnalysis:

    def __init__(self, client: OpenAI | AsyncOpenAI, context: str):
        self._client = client
        self.context = context

    @property
    def perscriptions_rqt(self) -> OAIRequest:
        """Extracts the perscriptions from a given document."""
        system_msg = oai_prompts.build_system_msg(
            oai_prompts.PERSCRIPTION_SYS_MSG,
            Perscriptions.model_json_schema(),
        )
        user_msg = oai_prompts.PERSCRIPTION_USER_MSG.format(self.context)
        response_schema = Perscriptions
        return OAIRequest(
            system_msg=system_msg, user_msg=user_msg, response_schema=response_schema
        )

    @property
    def metadata_rqt(self) -> OAIRequest:
        """Extracts the metadata from a given document."""
        system_msg = oai_prompts.build_system_msg(
            oai_prompts.METADATA_SYS_MSG.format(", ".join(specialties.keys())),
            AppointmentMeta.model_json_schema(),
        )
        user_msg = oai_prompts.METADATA_USER_MSG.format(self.context)
        response_schema = AppointmentMeta
        return OAIRequest(
            system_msg=system_msg, user_msg=user_msg, response_schema=response_schema
        )

    @property
    def followups_rqt(self) -> OAIRequest:
        """Extracts the follow up tasks from a given document."""
        system_msg = oai_prompts.build_system_msg(
            oai_prompts.FOLLOWUP_SYS_MSG, FollowUps.model_json_schema()
        )
        user_msg = oai_prompts.FOLLOWUP_USER_MSG.format(self.context)
        response_schema = FollowUps
        return OAIRequest(
            system_msg=system_msg, user_msg=user_msg, response_schema=response_schema
        )

    @property
    def summary_rqt(self) -> OAIRequest:
        """Extracts the summary from a given document."""
        system_msg = oai_prompts.build_system_msg(
            oai_prompts.SUMMARY_SYS_MSG, Summary.model_json_schema()
        )
        user_msg = oai_prompts.SUMMARY_USER_MSG.format(self.context)
        response_schema = Summary
        return OAIRequest(
            system_msg=system_msg, user_msg=user_msg, response_schema=response_schema
        )

    async def a_get_info(self) -> dict[str, Type[BaseModel]]:
        """Async function to extract info from a given document using the OpenAI API."""
        rqts = [
            self.perscriptions_rqt,
            self.metadata_rqt,
            self.followups_rqt,
            self.summary_rqt,
        ]
        responses = {}
        for rqt in rqts:
            logger.debug(f"Sending rqt for {rqt.response_schema.__name__}")
            response = await a_send_rqt(self._client, rqt)
            responses[rqt.response_schema.__name__] = response

        return responses


async def cache_data(key: str, value: str, expire: int = 3600):
    async with redis.client() as conn:
        await conn.set(key, value, ex=expire)


async def get_cached_data(key: str):
    async with redis.client() as conn:
        return await conn.get(key)


def insert_vector_db(context, params: dict[str, any]):
    try:
        v_db_params = {k: v for k, v in params.items() if k in METADATA_PARAMS}
        load_documents(context, v_db_params)
        logger.info(f"Context loaded into vector db")

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to insert into vector db with error {str(e)}",
        )


def insert_db(conn: connection, params: dict[str, any]):
    """All necessary relational db inserts are done here."""
    try:
        appt_id = upsert_appointment(conn, params)[0]
        logger.debug(f"Appointment inserted into db with id {appt_id}")

        params.update({"appointment_id": appt_id})
        upsert_prescription(conn, params)
        logger.debug(f"Prescriptions inserted into db")

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to insert into db with error {str(e)}"
        )


# dependencies=[Depends(get_current_user)]
router = APIRouter()


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...), x_user_id: str = Header(...)):
    # for now we just want to accept pdfs
    logger.debug(f"Uploading file {file.filename} for user {x_user_id}")
    if not file.content_type == "application/pdf":
        raise HTTPException(
            status_code=400, detail="Invalid file type. Please upload a PDF."
        )
    try:
        file_key = f"{x_user_id}/pdf/{uuid4()}_{file.filename}"
        logger.debug(f"Uploading file to s3 with key {file_key}")
        s3_client.upload_fileobj(
            file.file,
            S3_BUCKET_NAME,
            file_key,
            ExtraArgs={"ContentType": file.content_type},
        )
        s3_uri = f"s3://{S3_BUCKET_NAME}/{file_key}"
        return {"s3_uri": s3_uri}

    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})


@router.post("/analyze")
async def analyze_appointment(appt_rqt: ApptRqt, background_tasks: BackgroundTasks):
    s3_key = appt_rqt.data_location.split(f"s3://{S3_BUCKET_NAME}/")[1]
    logger.debug(f"Reading data from key = {s3_key}")

    loader = S3Reader(
        bucket=S3_BUCKET_NAME,
        key=s3_key,
        aws_access_id=AWS_ACCESS_KEY_ID,
        aws_access_secret=AWS_SECRET_ACCESS_KEY,
    )
    context = loader.load_data()
    text = " ".join([doc.text for doc in context])

    cache_key = create_hash_id(text, {"filename": appt_rqt.data_location})
    encoded_info = await get_cached_data(cache_key)
    info = json.loads(encoded_info) if encoded_info else None

    if not info:
        logger.debug(f"Cache miss for {cache_key}")
        appt = AppointmentAnalysis(client, context)
        info = await appt.a_get_info()
        info = {k: v.model_dump() for k, v in info.items()}  # make serializable
        logger.debug(f"Caching info = {pprint(info)}")
        await cache_data(cache_key, json.dumps(info))

    logger.info(f"info = {pprint(info)}")

    provider_info: dict[str, any] = info.get("AppointmentMeta", {}).get("provider_info")
    if not provider_info.get("npi"):
        provider_info["npi"] = await get_provider_id(provider_collection, provider_info)
    else:
        provider_info["npi"] = provider_info.get("npi")

    existing_record = get_provider_by_npi(provider_collection, provider_info["npi"])
    if not existing_record:
        logger.info(f"Provider not found in db - inserting record")
        background_tasks.add_task(upsert_provider, provider_collection, provider_info)

    # by here we need to have information verified
    params = {
        "user_id": appt_rqt.user_id,
        "provider_id": provider_info["npi"],  # this is going to be NPI
        "filename": appt_rqt.data_location,
        "summary": info.get("Summary", {}).get("summary"),
        "appointment_datetime": info.get("AppointmentMeta", {}).get("datetime"),
        "follow_ups": json.dumps(info.get("FollowUps", {})),
        "perscriptions": json.dumps(info.get("Perscriptions", {})),
    }

    background_tasks.add_task(insert_db, conn, params)
    background_tasks.add_task(insert_vector_db, context, params)

    return_provider_info = {
        "first_name": provider_info["first_name"],
        "last_name": provider_info["last_name"],
        "specialty": provider_info["specialty"],
    }

    response = {
        "prescriptions": info.get("Perscriptions", {}).get("drugs"),
        "provider_info": return_provider_info,
        "follow_ups": [task["task"] for task in info.get("FollowUps", {}).get("tasks")],
        "summary": info.get("Summary", {}).get("summary"),
    }
    return response


@router.get("/{user_id}")
async def get_appointments(user_id: int):
    results = []
    appointments = get_user_appointments(conn, user_id)
    for appt in appointments:
        formatted_datetime = appt["appointment_datetime"].strftime("%m/%d/%Y")
        item = {
            "id": appt["id"],
            "date": formatted_datetime,
            "summary": appt["summary"],
            "prescriptions": appt["perscriptions"],
            "follow_ups": [task["task"] for task in appt["follow_ups"]["tasks"]],
        }
        provider_info = provider_collection.find_one(
            {"npi": str(appt["provider_id"])},
            {"first_name": 1, "last_name": 1, "specialties": 1, "_id": 0},
        )
        provider_info["specialty"] = provider_info["specialties"][0]
        provider_info.pop("specialties")
        item.update({"provider_info": provider_info})
        results.append(item)

    return {"appointments": results}


if __name__ == "__main__":
    import asyncio

    client = AsyncOpenAI()

    context = SimpleDirectoryReader("/Users/nickocorriveau/dev/wilson/data").load_data()
    appt = AppointmentAnalysis(client, context)

    logger.info("Starting timer")
    start_time = time.time()
    info = asyncio.run(appt.a_get_info())
    print(info)
    logger.info(f"Time taken for analysis: {time.time() - start_time}")
