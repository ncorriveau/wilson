import io
import json
import logging.config
from contextlib import asynccontextmanager
from pprint import pprint
from typing import Dict

import aioredis
import yaml
from dotenv import load_dotenv
from fastapi import (
    BackgroundTasks,
    FastAPI,
    File,
    Header,
    HTTPException,
    Request,
    UploadFile,
)
from llama_index.core import SimpleDirectoryReader
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from pymongo import MongoClient
from PyPDF2 import PdfReader

load_dotenv()

from db.nosql_db import get_provider_by_npi, get_provider_id, upsert_provider
from db.relational_db import create_connection, create_pool, upsert_appointment
from db.vector_db import (
    build_index,
    create_hash_id,
    embed_model_llamaindex,
    load_documents,
    query_documents,
)

from .api_v1.endpoints.appointments import AppointmentAnalysis, FollowUps
from .api_v1.endpoints.follow_ups import get_followup_suggestions

with open("src/backend/configs/logging_config.yaml", "r") as config_file:
    logging_config = yaml.safe_load(config_file)

logging.config.dictConfig(logging_config)

logger = logging.getLogger(__name__)

METADATA_PARAMS = [
    "user_id",
    "provider_id",
    "filename",
    "appointment_date",
]


@asynccontextmanager
async def lifespan_async(app: FastAPI):
    db_pool = await create_pool()
    async with db_pool.acquire() as connection:
        yield {"conn": connection}
    await db_pool.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = create_connection()
    yield {"conn": conn}
    conn.close()


client = AsyncOpenAI()
redis = aioredis.from_url("redis://localhost")
mongo_db_client = MongoClient("mongodb://localhost:27017/")
db = mongo_db_client["wilson_ai"]
provider_collection = db.providers

app = FastAPI(
    title="Wilson AI API",
    description="""A FastAPI application to extract information from patient
    medical documents""",
    version="0.1.0",
    lifespan=lifespan,
)


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


def insert_db(request: Request, params):
    try:
        upsert_appointment(request.state.conn, params)
        logger.info(f"DB inserted Succesfully")

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to insert into db with error {str(e)}"
        )


class UserInfo(BaseModel):
    user_id: int = Field(..., description="The user id of the patient.")
    lat: float = Field(..., description="The latitude of the user.")
    lng: float = Field(..., description="The longitude of the user.")
    insurance_id: int = Field(..., description="The insurance id of the user.")


class ApptRqt(BaseModel):
    user_id: int = Field(..., description="The user id of the patient.")
    data_location: str = Field(..., description="The location of the data to analyze.")


class QueryRqt(BaseModel):
    user_id: int = Field(..., description="The user id of the patient.")
    query: str = Field(..., description="Query to be executed on the data")


class FollowUpRqt(BaseModel):
    user_info: UserInfo = Field(..., description="Information regarding the user.")
    follow_ups: FollowUps = Field(..., description="Follow up tasks to be executed.")


@app.post("/api/analyze_appointment/")
async def analyze_appointment(
    request: Request, appt_rqt: ApptRqt, background_tasks: BackgroundTasks
):
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

    background_tasks.add_task(insert_db, request, params)
    background_tasks.add_task(insert_vector_db, context, params)

    return info


@app.post("/api/query_data/")
async def query_data(query_rqt: QueryRqt):
    index = build_index(embed_model_llamaindex)
    response = query_documents(query_rqt.query, query_rqt.user_id, index)
    return response


@app.post("/api/get_follow_ups")
async def get_follow_ups(followup_rqt: FollowUpRqt):
    tasks = followup_rqt.follow_ups.tasks
    logging.info(f"Received tasks: {tasks}")
    follow_ups = await get_followup_suggestions(
        client, provider_collection, followup_rqt.user_info.model_dump(), tasks
    )
    return follow_ups


@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...), x_user_id: str = Header(...)):
    if not file.content_type == "application/pdf":
        raise HTTPException(
            status_code=400, detail="Invalid file type. Please upload a PDF."
        )
    content = await file.read()
    file_ = io.BytesIO(content)
    pdf_reader = PdfReader(file_)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()

    return {"filename": file.filename, "user_id": x_user_id}
