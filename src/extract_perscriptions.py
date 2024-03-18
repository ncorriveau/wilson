import logging
import sys
from typing import List

from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.llms.openai import OpenAI
from pydantic import BaseModel

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

EXTRACT_PERSCRIPTIONS_PROMPT = (
    """Generate a list of current medications the patient is taking."""
)
LLM = OpenAI(model="gpt-3.5-turbo", temperature=0.1)


class Drug(BaseModel):
    """A model to represent a given drug perscription. Technical name represents
    the name of the chemical compound, brand name represents the commercial
    name of the drug, and dosage represents the amount of the drug to be taken."""

    technical_name: str
    brand_name: str
    dosage: str


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
    print(response)
