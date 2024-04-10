import logging
import sys
import time
from typing import List, Type

from llama_index.core import SimpleDirectoryReader
from openai import AsyncOpenAI, OpenAI
from pydantic import BaseModel, ConfigDict, Field

from ..models.open_ai import prompts as oai_prompts
from ..models.open_ai.utils import OAIRequest, a_send_rqt

logging.basicConfig(stream=sys.stdout, level=logging.INFO)


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


class ProviderInfo(BaseModel):
    """A model to represent the provider's information."""

    provider_first_name: str = Field(
        ...,
        description="""The first name of the provider who wrote the note""",
    )
    provider_last_name: str = Field(
        ...,
        description="""The last name of the provider who wrote the note""",
    )
    provider_degree: str = Field(
        ...,
        description="""The medical degree of the provider, e.g. MD, DO, NP""",
    )


class AppointmentMeta(BaseModel):
    """A model to represent the metadata about the particular appointment."""

    provider_info: ProviderInfo = Field(
        ..., description="""Information about the provider"""
    )
    date: str = Field(
        ..., description="""The date of the appointment, in YYYY-MM-DD format"""
    )

    model_config = ConfigDict(
        json_schema_extra={
            "provider_info": {
                "provider_first_name": "John",
                "provider_last_name": "Doe",
                "provider_degree": "MD",
            },
            "date": "2023-10-10",
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
            oai_prompts.METADATA_SYS_MSG,
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
            logging.debug(f"Sending rqt for {rqt.response_schema.__name__}")
            response = await a_send_rqt(self._client, rqt)
            responses[rqt.response_schema.__name__] = response

        return responses


if __name__ == "__main__":
    import asyncio

    client = AsyncOpenAI()

    context = SimpleDirectoryReader("/Users/nickocorriveau/dev/wilson/data").load_data()
    appt = AppointmentAnalysis(client, context)

    logging.info("Starting timer")
    start_time = time.time()
    info = asyncio.run(appt.a_get_info())
    print(info)
    logging.info(f"Time taken for analysis: {time.time() - start_time}")
