import io
import json
from contextlib import asynccontextmanager
from typing import Dict

import aioredis
from dotenv import load_dotenv
from fastapi import FastAPI, File, Header, HTTPException, Request, UploadFile
from llama_index.core import SimpleDirectoryReader
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from PyPDF2 import PdfReader

load_dotenv()

from ..db.relational_db import create_connection, create_pool, insert_appointment
from ..db.vector_db import (
    build_index,
    create_hash_id,
    embed_model_llamaindex,
    load_documents,
    query_documents,
)
from .appointments import AppointmentAnalysis, FollowUps
from .follow_ups import get_followup_suggestions

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

app = FastAPI(
    title="Wilson AI API",
    description="""A FastAPI application to extract information from patient
    medical documents""",
    version="0.1.0",
    lifespan=lifespan,
)


# TODO: make this real
def fake_get_provider_id() -> int:
    return 1


# A utility to cache data
async def cache_data(key: str, value: str, expire: int = 3600):
    async with redis.client() as conn:
        await conn.set(key, value, ex=expire)


# A utility to get cached data
async def get_cached_data(key: str):
    async with redis.client() as conn:
        return await conn.get(key)


class ApptRqt(BaseModel):
    user_id: int = Field(..., description="The user id of the patient.")
    data_location: str = Field(..., description="The location of the data to analyze.")


class QueryRqt(BaseModel):
    user_id: int = Field(..., description="The user id of the patient.")
    query: str = Field(..., description="Query to be executed on the data")


class FollowUpRqt(BaseModel):
    user_id: int = Field(..., description="The user id of the patient.")
    follow_ups: FollowUps = Field(..., description="Follow up tasks to be executed.")


@app.post("/api/analyze_appointment/")
async def analyze_appointment(request: Request, appt_rqt: ApptRqt):
    # TODO: have this read in from an s3 location
    # documentation: https://github.com/run-llama/llama_index/blob/main/docs/docs/examples/data_connectors/simple_directory_reader_remote_fs.ipynb
    context = SimpleDirectoryReader(appt_rqt.data_location).load_data()
    text = " ".join([doc.text for doc in context])
    cache_key = create_hash_id(text, {"filename": appt_rqt.data_location})
    encoded_info = await get_cached_data(cache_key)
    info = json.loads(encoded_info) if encoded_info else None

    if not info:
        print(f"Cache miss for {cache_key}")
        appt = AppointmentAnalysis(client, context)
        info = await appt.a_get_info()
        info_serializable = {k: v.model_dump() for k, v in info.items()}
        encoded_info = json.dumps(info_serializable)
        await cache_data(cache_key, encoded_info)

    else:
        print(f"Cache hit for {cache_key}")

    provider_id = fake_get_provider_id()  # TODO: get this from the data

    params = {
        "user_id": appt_rqt.user_id,
        "provider_id": provider_id,
        "filename": appt_rqt.data_location,
        "summary": info.get("Summary", {}),
        "appointment_date": info.get("AppointmentMeta", {}).date,
        "follow_ups": info.get("FollowUps", {}).model_dump_json(),
        "perscriptions": info.get("Perscriptions", {}).model_dump_json(),
    }

    # insert data into vector db excludign some keys
    try:
        v_db_params = {k: v for k, v in params.items() if k in METADATA_PARAMS}
        load_documents(context, v_db_params)
        print(f"Context loaded into vector db")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # insert data into postgres db
    try:
        insert_appointment(request.state.conn, params)
        print(f"Inserted Succesfully")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return info


@app.post("/api/query_data/")
async def query_data(query_rqt: QueryRqt):
    index = build_index(embed_model_llamaindex)
    response = query_documents(query_rqt.query, query_rqt.user_id, index)
    return response


@app.post("/api/get_follow_ups")
async def get_follow_ups(request: Request, followup_rqt: FollowUpRqt):
    tasks = followup_rqt.follow_ups.tasks
    print(f"Received tasks: {tasks}")
    follow_ups = await get_followup_suggestions(
        client, request.state.conn, followup_rqt.user_id, tasks
    )
    return follow_ups


@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...), x_user_id: str = Header(...)):
    # TODO: add some user id authentication
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
