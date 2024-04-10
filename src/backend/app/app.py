import io
from contextlib import asynccontextmanager
from typing import Dict

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

app = FastAPI(
    title="Wilson AI API",
    description="""A FastAPI application to extract information from patient
    medical documents""",
    version="0.1.0",
    lifespan=lifespan,
)


def fake_get_provider_id(provider_info: Dict[str, str]) -> int:
    return 1


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
    appt = AppointmentAnalysis(client, context)
    info = await appt.a_get_info()

    provider_id = fake_get_provider_id(info.get("AppointmentMeta", {}).provider_info)

    params = {
        "user_id": appt_rqt.user_id,
        "provider_id": provider_id,
        "filename": appt_rqt.data_location,
        "summary": info.get("Summary", {}).summary,
        "appointment_date": info.get("AppointmentMeta", {}).date,
        "follow_ups": info.get("FollowUps", {}).model_dump_json(),
        "perscriptions": info.get("Perscriptions", {}).model_dump_json(),
    }

    # insert data into vector db excludign some keys
    v_db_params = {k: v for k, v in params.items() if k in METADATA_PARAMS}
    load_documents(context, v_db_params)
    print(f"Context loaded into vector db")

    # insert data into postgres db
    try:
        insert_appointment(request.state.conn, params)
        print(f"Inserted Succesfully")

    except Exception as e:
        print(f"Error: {e}")

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
