import logging
import sys
from typing import List

from llama_index.core import SimpleDirectoryReader
from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

EXTRACT_PERSCRIPTIONS_PROMPT = (
    """Generate a list of current medications the patient is taking."""
)
# LLM = OpenAI(model="gpt-3.5-turbo", temperature=0.1)


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


SYSTEM_MESSAGE = f"""You are an expert AI assistant for medical practitioners. You will assist in analyzing 
medical records and returning a list of current medications the patient is taking in a valid JSON format. You just return 
valid JSON objects that contain the technical name, brand name, and instructions for each drug found that follows
the schema below:

JSON Schema: 
{Perscriptions.model_json_schema()}
"""
USER_MESSAGE = """Extract the perscribed medications from the doctor note below and return a list of current medications the patient is taking in a valid JSON format. 
Doctor Note: 
{}"""
ASSISTANT_MESSAGE = "```json"


def extract_perscriptions(client: OpenAI, note: str) -> Perscriptions:
    response = client.chat.completions.create(
        model="gpt-4",
        max_tokens=1000,
        temperature=0.1,
        stop=["```"],
        messages=[
            {"role": "system", "content": SYSTEM_MESSAGE},
            {"role": "user", "content": USER_MESSAGE.format(note)},
            {"role": "assistant", "content": ASSISTANT_MESSAGE},
        ],
        # response_format="json_object",
    )
    return Perscriptions.model_validate_json(response.choices[0].message.content)


if __name__ == "__main__":
    client = OpenAI()
    document = SimpleDirectoryReader("data").load_data()
    response = extract_perscriptions(client, document)

    TRUE_NAMES = {"flonase", "nexium", "naprosyn", "astelin", "desyrel"}
    TEST_NAMES = set()

    for drug in response.drugs:
        print(f"Checking {drug.brand_name.lower()}")
        assert drug.brand_name.lower() in TRUE_NAMES
        TEST_NAMES.add(drug.brand_name.lower())

    assert TEST_NAMES == TRUE_NAMES
    print("All tests passed!")
