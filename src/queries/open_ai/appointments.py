import logging
import sys
from typing import Type

from llama_index.core import SimpleDirectoryReader
from openai import OpenAI
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
    response_schema: Type[BaseModel] = Field(
        ..., description="Pydantic model specifying JSON response schema."
    )

    # prompts
    system_msg: str = Field(default="")
    user_msg: str = Field(default="")
    assistant_msg: str = Field(default="```json")

    # optional parameters
    response_format: dict = Field(default={"type": "json_object"})


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
        response_format={"type": "json_object"},
    )
    return rqt.response_schema.model_validate_json(response.choices[0].message.content)


def extract_perscriptions(context: str) -> OAIRequest:
    """Extracts the perscriptions from a given document."""
    system_msg = oai_prompts.build_system_msg(
        oai_prompts.PERSCRIPTION_SYS_MSG, appointment.Perscriptions.model_json_schema()
    )
    user_msg = oai_prompts.PERSCRIPTION_USER_MSG.format(context)
    response_schema = appointment.Perscriptions
    return OAIRequest(
        system_msg=system_msg, user_msg=user_msg, response_schema=response_schema
    )


if __name__ == "__main__":
    client = OpenAI()
    context = SimpleDirectoryReader("data").load_data()
    request = extract_perscriptions(context)
    response = send_rqt(client, request)
    print(response)
