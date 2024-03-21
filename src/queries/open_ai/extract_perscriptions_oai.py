import logging
import sys
from typing import Type

from llama_index.core import SimpleDirectoryReader
from openai import OpenAI
from pydantic import BaseModel, Field

import data_models.appointment_summary as appointment_sum
from prompts import open_ai as oai_prompts

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))


class OAIRequest(BaseModel):
    client: OpenAI = Field(..., description="The OpenAI client to use.")

    # required parameters
    model: str = Field(..., default="gpt-4-1106-preview")
    max_tokens: int = Field(..., default=1000)
    temperature: float = Field(..., default=0.1)
    stop: list = Field(..., default=["```"])

    # prompts
    system_msg: str = Field(..., default="")
    user_msg: str = Field(..., default="")
    assistant_msg: str = Field(..., default="```json")

    # optional parameters
    response_format: dict = Field(default={"type": "json_object"})


def extract_info(
    client: OpenAI, rqt: OAIRequest, model: Type[BaseModel]
) -> Type[BaseModel]:
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
    return model.model_validate_json(response.choices[0].message.content)


# def extract_perscriptions(client: OpenAI, context: str) -> OAIRequest:
#     """Extracts the perscriptions from a given document."""
#     system_msg = build_system_msg(PERSCRIPTION_SYS_MSG, Perscriptions.model_json_schema())
#     user_msg = PERSCRIPTION_USER_MSG.format(document)
#     messages = Messages(system=system_msg, user=user_msg)
#     response = extract_info(client, messages, Perscriptions)
#     return response

if __name__ == "__main__":
    client = OpenAI()
    document = SimpleDirectoryReader("data").load_data()

    # schema = Perscriptions.model_json_schema()
    # response = extract_perscriptions(client, document)

    # TRUE_NAMES = {"flonase", "nexium", "naprosyn", "astelin", "desyrel"}
    # TEST_NAMES = set()

    # for drug in response.drugs:
    #     print(f"Checking {drug.brand_name.lower()}")
    #     assert drug.brand_name.lower() in TRUE_NAMES
    #     TEST_NAMES.add(drug.brand_name.lower())

    # assert TEST_NAMES == TRUE_NAMES
    # print("All tests passed!")
