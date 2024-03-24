from fastapi import FastAPI
from llama_index.core import SimpleDirectoryReader
from openai import OpenAI
from pydantic import BaseModel

from queries.open_ai.appointments import AppointmentAnalysis

client = OpenAI()

app = FastAPI(
    title="Wilson AI API",
    description="""A FastAPI application to extract information from patient
    medical documents""",
    version="0.1.0",
)


class ApptRqt(BaseModel):
    data_location: str


@app.post("/api/analyze_appointment/")
def analyze_appointment(appt_rqt: ApptRqt):
    if not appt_rqt.data_location:
        return {"error": "No data provided"}

    context = SimpleDirectoryReader("../data").load_data()
    appt = AppointmentAnalysis(client, context)
    info = appt.get_info()
    return info
