from typing import Dict

from fastapi import FastAPI
from llama_index.core import SimpleDirectoryReader
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from typing_extensions import Annotated

from db import create_connection, insert_appointment
from queries.open_ai.appointments import AppointmentAnalysis
from vector_db import (
    build_index,
    embed_model_llamaindex,
    load_documents,
    query_documents,
)

client = AsyncOpenAI()
params_to_exclude = [
    "user_id",
    "provider_id",
    "filename",
    "appointment_date",
]

app = FastAPI(
    title="Wilson AI API",
    description="""A FastAPI application to extract information from patient
    medical documents""",
    version="0.1.0",
)


def fake_get_provider_id(provider_info: Dict[str, str]) -> int:
    return 1


class ApptRqt(BaseModel):
    user_id: int = Field(..., description="The user id of the patient.")
    data_location: str = Field(..., description="The location of the data to analyze.")


class QueryRqt(BaseModel):
    user_id: int = Field(..., description="The user id of the patient.")
    query: str = Field(..., description="Query to be executed on the data")


@app.post("/api/analyze_appointment/")
async def analyze_appointment(appt_rqt: ApptRqt):
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

    # insert data into vector db
    v_db_params = {k: v for k, v in params.items() if k not in params_to_exclude}
    load_documents(
        appt_rqt.data_location, v_db_params
    )  # we load the document twice.should fix this later
    print(f"Context loaded into vector db")

    # insert data into postgres db
    conn = create_connection()
    try:
        insert_appointment(conn, params)
        print(f"Inserted Succesfully")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

    print(f"Done - returning")
    return info


@app.post("/api/query_data/")
async def query_data(query_rqt: QueryRqt):
    index = build_index(embed_model_llamaindex)
    response = query_documents(query_rqt.query, index)
    return response
