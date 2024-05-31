"""
A file to hold the common pydantic classes needed for the api to keep the 
actual logic files a bit cleaner. 
"""

from datetime import datetime
from enum import Enum
from typing import List, Type

from pydantic import BaseModel, ConfigDict, Field, validator

from ..db.relational_db import create_connection, get_specialties


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

#### APPOINTMENT MODELS ####


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
    model_config = ConfigDict(
        json_schema_extra={
            "summary": "Routine visit for annual physical. No major health concerns, but the provider noticed you had an elevated heart rate. Follow ups include more exercise and a check in on vitals in a month."
        }
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


class ApptRqt(BaseModel):
    user_id: int = Field(..., description="The user id of the patient.")
    data_location: str = Field(
        ..., description="The location of the data to analyze. Must be a valid s3 uri."
    )


#### FOLLOW UP MODELS ####
class TaskSpecialty(BaseModel):
    """A model to represent the correct specialty to book with given an associated follow up tasks"""

    specialty: SpecialtyEnum | None = Field(  # type: ignore
        default=None, description="""The specialty of the provider"""
    )


class UserInfo(BaseModel):
    user_id: int = Field(..., description="The user id of the patient.")
    lat: float = Field(..., description="The latitude of the user.")
    lng: float = Field(..., description="The longitude of the user.")
    insurance_id: int = Field(..., description="The insurance id of the user.")


class FollowUpRqt(BaseModel):
    user_info: UserInfo = Field(..., description="Information regarding the user.")
    follow_ups: FollowUps = Field(..., description="Follow up tasks to be executed.")


### PRESCRIPTION MODELS ###
class ProviderInfo(BaseModel):
    firstName: str = Field(
        ..., description="The id of the provider.", alias="first_name"
    )
    lastName: str = Field(
        ..., description="The name of the provider.", alias="last_name"
    )
    specialty: SpecialtyEnum = Field(..., description="The specialty of the provider.")  # type: ignore


class PrescriptionResponse(BaseModel):
    id: int = Field(..., description="The id of the prescription.")
    brandName: str = Field(
        ..., description="The brand name of the prescription.", alias="brand_name"
    )
    technicalName: str = Field(
        ...,
        description="The technical name of the prescription.",
        alias="technical_name",
    )
    instructions: str = Field(..., description="The instructions for the prescription.")
    providerInfo: ProviderInfo = Field(
        ...,
        description="The provider information for the prescription.",
        alias="provider_info",
    )
    isActive: bool = Field(
        ..., description="The active status of the prescription.", alias="active_flag"
    )

    class Config:
        allow_population_by_field_name = True


class PrescriptionRequest(BaseModel):
    id: int = Field(..., description="The id of the prescription.")
    active_flag: bool = Field(
        ..., description="The active status of the prescription.", alias="isActive"
    )
