import logging
import sys
from typing import List

from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.llms.openai import OpenAI
from pydantic import BaseModel, Field

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

EXTRACT_PERSCRIPTIONS_PROMPT = (
    """Generate a list of current medications the patient is taking."""
)
LLM = OpenAI(model="gpt-3.5-turbo", temperature=0.1)


class Drug(BaseModel):
    """A model to represent a given drug perscription. Technical name represents
    the name of the chemical compound, brand name represents the commercial
    name of the drug, and instructions represents additional notes about the drugs usage.
    """

    technical_name: str
    brand_name: str
    instructions: str


class Perscriptions(BaseModel):
    """A model to represent the perscriptions extracted from a given document."""

    drugs: List[Drug]


def extract_perscriptions(index, llm):
    query_engine = index.as_query_engine(
        output_cls=Perscriptions, response_mode="compact", llm=llm
    )
    response = query_engine.query(EXTRACT_PERSCRIPTIONS_PROMPT)
    return response


if __name__ == "__main__":
    document = SimpleDirectoryReader("data").load_data()
    index = VectorStoreIndex.from_documents(
        document,
    )
    response = extract_perscriptions(index, LLM)
    TRUE_NAMES = {"flonase", "nexium", "naprosyn", "astelin", "desyrel"}
    TEST_NAMES = set()

    for drug in response.drugs:
        print(f"Checking {drug.brand_name.lower()}")
        assert drug.brand_name.lower() in TRUE_NAMES
        TEST_NAMES.add(drug.brand_name.lower())

    assert TEST_NAMES == TRUE_NAMES
    print("All tests passed!")