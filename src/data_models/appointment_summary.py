from typing import List

from pydantic import BaseModel, ConfigDict, Field


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


class AppointmentMeta(BaseModel):
    """A model to represent the metadata about the particular appointment."""

    dr_name: str = Field(..., description="""The name of the doctor""")
    date: str = Field(
        ..., description="""The date of the appointment, in YYYY-MM-DD format"""
    )

    model_config = ConfigDict(
        json_schema_extra={
            "dr_name": "Dr. Oz",
            "date": "2023-10-10",
        },
    )