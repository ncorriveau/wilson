import logging
import sys
from dataclasses import dataclass
from typing import List, Type

from llama_index.core import SimpleDirectoryReader
from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

PERSCRIPTION_SYS_MSG = """You will assist in analyzing medical records and returning a list of current medications the patient is taking in a valid JSON format. You just return 
valid JSON objects that contain the technical name, brand name, and instructions for each drug found."""

PERSCRIPTION_USER_MSG = """Extract the perscribed medications from the doctor note below and return a list of current medications the patient is taking in a valid JSON format. 
Doctor Note: 
{}"""

METADATA_SYS_MSG = """return metadata about the particular appointment in a valid JSON format. The JSON objects must contain the doctor's name and the date of the appointment. If you are unsure, please respond with an empty string for each category"""

METADATA_USER_MSG = """Extract the doctor's name and the date of the appointment from the doctors note below and return the information in valid JSON format.
Doctor Note:
{}"""


def build_system_msg(msg: str, schema: dict[str]) -> str:
    """helper function to build system messages. The msg should contain more specific instructions about the task,
    while the schema should match what you want your response JSON schema to look like
    """
    return f"""You are an expert AI assistant for medical practitioners. You will assist in analyzing medical records, extracting information, and returning the information in valid JSON format. Specifically, please complete the following:
            {msg}. Follow the JSON schema provided below to ensure the information is returned in the correct format.
            JSON Schema: 
            {schema}"""


@dataclass
class Messages:
    system: str = ""
    user: str = ""
    assistant: str = "```json"


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


def extract_info(
    client: OpenAI, messages: Messages, model: Type[BaseModel]
) -> Type[BaseModel]:
    """Extracts information from a given document using the OpenAI API."""
    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        max_tokens=1000,
        temperature=0.1,
        stop=["```"],
        messages=[
            {"role": "system", "content": messages.system},
            {"role": "user", "content": messages.user},
            {"role": "assistant", "content": messages.assistant},
        ],
        response_format={"type": "json_object"},
    )
    return model.model_validate_json(response.choices[0].message.content)


if __name__ == "__main__":
    client = OpenAI()
    document = SimpleDirectoryReader("data").load_data()
    messages = Messages(
        system=build_system_msg(METADATA_SYS_MSG, AppointmentMeta.model_json_schema()),
        user=METADATA_USER_MSG.format(document),
    )
    response = extract_info(client, messages, AppointmentMeta)
    print(response)
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
