import logging
import sys
import time
from typing import Any, Dict, Type

from llama_index.core import SimpleDirectoryReader
from openai import AsyncOpenAI, OpenAI
from pydantic import BaseModel, Field

import src.data_models.appointment_summary as appointment
from src.prompts import open_ai as oai_prompts

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))


class OAIRequest(BaseModel):
    """A model to represent a given request to the OpenAI API."""

    # required parameters
    model: str = Field(default="gpt-4-1106-preview")
    max_tokens: int = Field(default=1000)
    temperature: float = Field(default=0.1)
    stop: list = Field(default=["```"])

    # prompts
    system_msg: str = Field(default="")
    user_msg: str = Field(default="")
    assistant_msg: str = Field(default="```json")

    # optional parameters - only available for recent models
    response_schema: Type[BaseModel] | None = Field(
        default=None, description="Pydantic model specifying JSON response schema."
    )
    response_format: dict = Field(default={"type": "json_object"})
    tools: list = Field(default=[])
    tool_choices: Dict[str, Any] | None = Field(
        default=None, description="Parameter to force tool choices."
    )


def send_rqt(client: OpenAI, rqt: OAIRequest) -> Type[BaseModel]:
    """Extracts information from a given document using the OpenAI API."""
    response = client.chat.completions.create(
        model=rqt.model,
        max_tokens=rqt.max_tokens,
        temperature=rqt.temperature,
        stop=rqt.stop,
        messages=[
            {"role": "system", "content": rqt.system_msg},
            {"role": "user", "content": rqt.user_msg},
            {"role": "assistant", "content": rqt.assistant_msg},
        ],
        tools=rqt.tools,
        response_format={"type": "json_object"},
    )

    if not rqt.response_schema:
        return response.choices[0].message.content

    return rqt.response_schema.model_validate_json(response.choices[0].message.content)


async def a_send_rqt(client: AsyncOpenAI, rqt: OAIRequest) -> Type[BaseModel]:
    """Extracts information from a given document using the OpenAI API."""
    response = await client.chat.completions.create(
        model=rqt.model,
        max_tokens=rqt.max_tokens,
        temperature=rqt.temperature,
        stop=rqt.stop,
        messages=[
            {"role": "system", "content": rqt.system_msg},
            {"role": "user", "content": rqt.user_msg},
            {"role": "assistant", "content": rqt.assistant_msg},
        ],
        response_format={"type": "json_object"},
    )

    if not rqt.response_schema:
        return response.choices[0].message.content

    return rqt.response_schema.model_validate_json(response.choices[0].message.content)


class AppointmentAnalysis:

    def __init__(self, client: OpenAI | AsyncOpenAI, context: str):
        self._client = client
        self.context = context

    @property
    def perscriptions_rqt(self) -> OAIRequest:
        """Extracts the perscriptions from a given document."""
        system_msg = oai_prompts.build_system_msg(
            oai_prompts.PERSCRIPTION_SYS_MSG,
            appointment.Perscriptions.model_json_schema(),
        )
        user_msg = oai_prompts.PERSCRIPTION_USER_MSG.format(self.context)
        response_schema = appointment.Perscriptions
        return OAIRequest(
            system_msg=system_msg, user_msg=user_msg, response_schema=response_schema
        )

    @property
    def metadata_rqt(self) -> OAIRequest:
        """Extracts the metadata from a given document."""
        system_msg = oai_prompts.build_system_msg(
            oai_prompts.METADATA_SYS_MSG,
            appointment.AppointmentMeta.model_json_schema(),
        )
        user_msg = oai_prompts.METADATA_USER_MSG.format(self.context)
        response_schema = appointment.AppointmentMeta
        return OAIRequest(
            system_msg=system_msg, user_msg=user_msg, response_schema=response_schema
        )

    @property
    def followups_rqt(self) -> OAIRequest:
        """Extracts the follow up tasks from a given document."""
        system_msg = oai_prompts.build_system_msg(
            oai_prompts.FOLLOWUP_SYS_MSG, appointment.FollowUps.model_json_schema()
        )
        user_msg = oai_prompts.FOLLOWUP_USER_MSG.format(self.context)
        response_schema = appointment.FollowUps
        return OAIRequest(
            system_msg=system_msg, user_msg=user_msg, response_schema=response_schema
        )

    @property
    def summary_rqt(self) -> OAIRequest:
        """Extracts the summary from a given document."""
        system_msg = oai_prompts.build_system_msg(
            oai_prompts.SUMMARY_SYS_MSG, appointment.Summary.model_json_schema()
        )
        user_msg = oai_prompts.SUMMARY_USER_MSG.format(self.context)
        response_schema = appointment.Summary
        return OAIRequest(
            system_msg=system_msg, user_msg=user_msg, response_schema=response_schema
        )

    async def get_info(self) -> dict[str, Type[BaseModel]]:
        """Extracts information from a given document using the OpenAI API."""
        rqts = [
            self.perscriptions_rqt,
            self.metadata_rqt,
            self.followups_rqt,
            self.summary_rqt,
        ]
        responses = {}
        for rqt in rqts:
            logging.debug(f"Sending rqt for {rqt.response_schema.__name__}")
            response = await send_rqt(self._client, rqt)
            responses[rqt.response_schema.__name__] = response

        return responses


if __name__ == "__main__":
    import asyncio

    client = AsyncOpenAI()

    context = SimpleDirectoryReader("../data").load_data()
    appt = AppointmentAnalysis(client, context)

    logging.info("Starting timer")
    start_time = time.time()
    info = asyncio.run(appt.get_info())
    print(info)
    logging.info(f"Time taken for analysis: {time.time() - start_time}")

    # for key, value in info.items():
    #     logging.info(f"{key}: {value}")
