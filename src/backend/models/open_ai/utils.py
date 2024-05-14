import logging
import sys
from typing import Any, Dict, Type

from openai import AsyncOpenAI, OpenAI
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class OAIRequest(BaseModel):
    """A model to represent a given request to the OpenAI API."""

    # required parameters
    model: str = Field(default="gpt-4o")
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
    response_format: dict | None = Field(default=None)
    tools: list | None = Field(
        default=None, description="Tools to use for the request."
    )
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
        response_format={"type": "json_object"} if rqt.model != "gpt-4" else None,
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
        tools=rqt.tools,
        response_format={"type": "json_object"} if rqt.model != "gpt-4" else None,
    )

    if not rqt.response_schema:
        return response.choices[0].message.content

    return rqt.response_schema.model_validate_json(response.choices[0].message.content)
