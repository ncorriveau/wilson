import json
import logging
import time
from datetime import datetime
from enum import Enum
from pprint import pprint
from typing import List, Type

import aioredis
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from llama_index.core import SimpleDirectoryReader
from openai import AsyncOpenAI, OpenAI
from psycopg2.extensions import connection
from pydantic import BaseModel, ConfigDict, Field, validator
from pymongo import MongoClient

from ....models.open_ai import prompts as oai_prompts
from ....models.open_ai.utils import OAIRequest, a_send_rqt
from ...db.nosql_db import get_provider_by_npi, get_provider_id, upsert_provider
from ...db.relational_db import create_connection, get_specialties, upsert_appointment
from ...db.vector_db import create_hash_id, load_documents
from ...deps import get_current_user

logger = logging.getLogger(__name__)

METADATA_PARAMS = [
    "user_id",
    "provider_id",
    "filename",
    "appointment_date",
]


def make_specialty_enum() -> Type[Enum]:
    """
    Creates an Enum class for the specialties based off database values.
    This will return values that are specialty abbreviation: description
    for each value in the db e.g. SPORTS: Sports Medicine
    """
    specialties = get_specialties(create_connection())
    return Enum("SpecialtyEnum", {k: k for k in specialties.keys()})


specialties = get_specialties(create_connection())
SpecialtyEnum: Enum = make_specialty_enum()


class Drug(BaseModel):
    """A model to represent a given drug perscription."""

    technical_name: str = Field(
        ...,
        description="""Technical name represents the name of the chemical compound""",
    )
    brand_name: str = Field(
        ..., description="""Brand name represents the commercial name of the drug"""
    )
    instructions: str = Field(
        ...,
        description="""Instructions represents additional notes about the drugs usage""",
    )


class Perscriptions(BaseModel):
    """A model to represent the perscriptions extracted from a given document."""

    drugs: List[Drug]
    model_config = ConfigDict(
        json_schema_extra={
            "drugs": [
                {
                    "technical_name": "Fluticasone",
                    "brand_name": "Flonase",
                    "instructions": "Take one spray in each nostril once daily.",
                },
                {
                    "technical_name": "Augmentin",
                    "brand_name": "amoxicillin",
                    "instructions": "Take a 500-mg tablet twice daily",
                },
            ]
        }
    )


class FollowUp(BaseModel):
    """A model to represent the follow up tasks prescribed by the doctor."""

    task: str = Field(
        ...,
        description="""A referral appointment or test prescribed by the doctor. For example, 'Schedule an appointment with a ENT specialist.'""",
    )


class FollowUps(BaseModel):
    """A model to represent the follow up tasks prescribed by the doctor."""

    tasks: List[FollowUp]
    model_config = ConfigDict(
        json_schema_extra={
            "tasks": [
                {"task": "Schedule an appointment with a ENT specialist."},
                {"task": "Get a blood test for cholesterol."},
            ]
        }
    )


class Summary(BaseModel):
    """A model to represent the summary of the doctor's note."""

    summary: str = Field(
        ...,
        description="""A summary of the doctor's note, including the patient's condition and the doctor's recommendations""",
    )


class Location(BaseModel):
    """A model to represent the location of the appointment"""

    street: str = Field(
        ...,
        description="""The street address""",
    )
    city: str = Field(
        ...,
        description="""The city""",
    )
    state: str = Field(
        ...,
        description="""The state""",
    )
    zip_code: str = Field(
        ...,
        description="""The zip code""",
    )


class ProviderInfo(BaseModel):
    """A model to represent the provider's information."""

    first_name: str = Field(
        ...,
        description="""The first name of the provider who wrote the note""",
    )
    last_name: str = Field(
        ...,
        description="""The last name of the provider who wrote the note""",
    )
    degree: str = Field(
        ...,
        description="""The medical degree of the provider, e.g. MD, DO, NP""",
    )
    email: str | None = Field(
        default=None,
        description="""The email of the provider""",
    )
    phone_number: str | None = Field(
        default=None,
        description="""The phone number of the provider""",
    )
    npi: str | None = Field(
        default=None,
        description="""The NPI number of the provider who wrote the note""",
    )
    location: Location | None = Field(
        default=None, description="""The location of the appointment"""
    )

    # we are using this so we can explicitly pass in legal values to the prompt
    # in a dynamic manner. however, we just want the actual value (not the enum)
    specialty: SpecialtyEnum | None = Field(  # type: ignore
        default=None, description="""The specialty of the provider"""
    )

    class Config:
        use_enum_values = True  # ensure we can serialize


class AppointmentMeta(BaseModel):
    """A model to represent the metadata about the particular appointment."""

    provider_info: ProviderInfo = Field(
        ..., description="""Information about the provider"""
    )
    datetime: str = Field(
        ..., description="""The date of the appointment, in YYYY-MM-DD H:M format"""
    )

    @validator("datetime")
    def validate_date(cls, val):
        try:
            return datetime.strptime(val, "%Y-%m-%d %H:%M").strftime("%Y-%m-%d %H:%M")
        except ValueError:
            raise ValueError("Incorrect date format, should be YYYY-MM-DD H:M")

    model_config = ConfigDict(
        json_schema_extra={
            "provider_info": {
                "provider_first_name": "John",
                "provider_last_name": "Doe",
                "provider_degree": "MD",
                "provider_NPI": "1234567890",
                "provider_address": {
                    "street": "123 Main St",
                    "city": "Anytown",
                    "state": "NY",
                    "zip_code": "12345",
                },
                "provider_specialty": "ENT",
            },
            "datetime": "2023-10-10 20:16",
        },
    )


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


class ApptRqt(BaseModel):
    user_id: int = Field(..., description="The user id of the patient.")
    data_location: str = Field(..., description="The location of the data to analyze.")


client = AsyncOpenAI()
redis = aioredis.from_url("redis://localhost")
mongo_db_client = MongoClient("mongodb://localhost:27017/")
db = mongo_db_client["wilson_ai"]
provider_collection = db.providers
conn = create_connection()


async def cache_data(key: str, value: str, expire: int = 3600):
    async with redis.client() as conn:
        await conn.set(key, value, ex=expire)


async def get_cached_data(key: str):
    async with redis.client() as conn:
        return await conn.get(key)


def insert_vector_db(context, params):
    try:
        v_db_params = {k: v for k, v in params.items() if k in METADATA_PARAMS}
        load_documents(context, v_db_params)
        logger.info(f"Context loaded into vector db")

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to insert into vector db with error {str(e)}",
        )


def insert_db(conn: connection, params):
    try:
        upsert_appointment(conn, params)
        logger.info(f"DB inserted Succesfully")

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to insert into db with error {str(e)}"
        )


router = APIRouter(dependencies=[Depends(get_current_user)])


@router.post("/api/analyze_appointment/")
async def analyze_appointment(appt_rqt: ApptRqt, background_tasks: BackgroundTasks):
    # TODO: have this read in from an s3 location
    # documentation: https://github.com/run-llama/llama_index/blob/main/docs/docs/examples/data_connectors/simple_directory_reader_remote_fs.ipynb
    context = SimpleDirectoryReader(appt_rqt.data_location).load_data()
    text = " ".join([doc.text for doc in context])

    cache_key = create_hash_id(text, {"filename": appt_rqt.data_location})
    encoded_info = await get_cached_data(cache_key)
    info = json.loads(encoded_info) if encoded_info else None

    if not info:
        logger.debug(f"Cache miss for {cache_key}")
        appt = AppointmentAnalysis(client, context)
        info = await appt.a_get_info()
        info = {k: v.model_dump() for k, v in info.items()}  # make serializable
        await cache_data(cache_key, json.dumps(info))

    logger.info(f"info = {pprint(info)}")

    provider_info = info.get("AppointmentMeta", {}).get("provider_info")
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

    return info


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
