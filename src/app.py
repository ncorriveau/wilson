from fastapi import FastAPI
from llama_index.core import SimpleDirectoryReader
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from typing_extensions import Annotated

from db import CREATE_TABLE_QUERY, create_connection, create_table, insert_appointment
from queries.open_ai.appointments import AppointmentAnalysis

client = AsyncOpenAI()

app = FastAPI(
    title="Wilson AI API",
    description="""A FastAPI application to extract information from patient
    medical documents""",
    version="0.1.0",
)


class ApptRqt(BaseModel):
    user_id: str = Field(..., description="The user id of the patient.")
    data_location: str = Field(..., description="The location of the data to analyze.")


@app.post("/api/analyze_appointment/")
async def analyze_appointment(appt_rqt: ApptRqt):
    context = SimpleDirectoryReader(appt_rqt.data_location).load_data()
    appt = AppointmentAnalysis(client, context)
    info = await appt.get_info()

    params = {
        "filename": appt_rqt.data_location,
        "summary": info.get("Summary", {}).summary,
        "provider_name": info.get(
            "AppointmentMeta", {}
        ).dr_name,  # TODO: update this to provider name
        "appointment_date": info.get("AppointmentMeta", {}).date,
        "follow_ups": info.get("FollowUps", {}).model_dump_json(),
        "perscriptions": info.get("Perscriptions", {}).model_dump_json(),
    }

    conn = create_connection()
    try:
        insert_appointment(conn, params)
        print(f"Inserted Succesfully")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

    print(f"Returning type: {type(info)}")
    return info
