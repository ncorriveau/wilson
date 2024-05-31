"""Functions to aid in the indexing and storing of data in a vector database """

import logging
import os
from collections import defaultdict
from pprint import pprint
from typing import Any, Dict, List

import chromadb
import chromadb.utils.embedding_functions as embedding_functions
import pandas as pd
from chromadb import Collection
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.base.response.schema import Response
from llama_index.core.indices.vector_store.base import VectorStoreIndex
from llama_index.core.schema import Document
from llama_index.core.vector_stores import MetadataFilter, MetadataFilters
from llama_index.vector_stores.chroma import ChromaVectorStore

from ..utils.utils import create_hash_id

_logger = logging.getLogger(__name__)

os.environ["TOKENIZERS_PARALLELISM"] = "false"

COLLECTION = "appointment_oai"
DB_PATH = "/Users/nickocorriveau/dev/wilson/chroma_db"
HF_EMBED_MODEL = "BAAI/bge-base-en-v1.5"

CHAT_W_DATA_SYS_MSG = """You are a word class medical physician who is also an expert in Q&A and you will assist in analyzing this patient's medical records
and responding to their questions to the best of your ability. For each query, you will be provided with the most relevant context
from the patients medical records. Additionally, piece of context will have information about the date of the appointment and the provider's name."""

CHAT_W_DATA_USER_MSG = """Based on the following context, please answer the 
query to the best of your ability. 
Please note that the context will contain metadata about the date of the appointment and the provider's name.
If the provider name and date are the same, you can assume it is from the same appointment. 
Query: {}
Context: {}
"""

embed_model_oai = embedding_functions.OpenAIEmbeddingFunction(
    api_key=os.environ["OPENAI_API_KEY"],
    model_name="text-embedding-3-small",
)

EMBED_MODEL = embed_model_oai


def load_documents(documents: List[Document], metadata: Dict[Any, Any]) -> None:
    """Load documents from a directory into the vector database."""
    client = chromadb.PersistentClient(path=DB_PATH)
    collection = client.get_or_create_collection(
        name=COLLECTION, embedding_function=EMBED_MODEL
    )

    collection.upsert(
        documents=[document.text for document in documents],
        metadatas=[metadata for _ in documents],
        ids=[create_hash_id(document.text, metadata) for document in documents],
    )
    return


def get_context(query: str, user_id: int, collection: Collection) -> Dict[str, Any]:
    """Get context for the query."""
    result = collection.query(
        query_texts=query,
        include=["documents", "metadatas", "distances"],
        where={"user_id": user_id},
    )
    return result


def structure_context(context: Dict[str, Any]) -> str:
    """
    From a chroma db response, organize the information such that context
    from the same provider / appointment is grouped together and sorted by date
    (latest to earliest). This will provide an organized way of presenting
    the information to the LLM in the prompt.
    """
    result_dict = defaultdict(list)
    for i, doc in enumerate(context["documents"][0]):
        metadata = context["metadatas"][0][i]
        result_dict["provider_name"].append(metadata["provider_name"])
        result_dict["appointment_date"].append(metadata["appointment_datetime"])
        result_dict["context"].append(doc)

    df = pd.DataFrame(result_dict)
    df = (
        df.assign(appointment_date=pd.to_datetime(df["appointment_date"]))
        .groupby(["provider_name", "appointment_date"])["context"]
        .agg(" ".join)
        .reset_index()
        .sort_values(by=["appointment_date"])
    )
    df["formatted_row"] = df.apply(
        lambda x: f"{x['provider_name']}, {x['appointment_date']}:\n{x['context']}",
        axis=1,
    )
    return "\n".join(df["formatted_row"].to_list())


def build_index(embed_model: Any) -> VectorStoreIndex:
    db = chromadb.PersistentClient(path=DB_PATH)
    chroma_collection = db.get_or_create_collection(COLLECTION)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    index = VectorStoreIndex.from_vector_store(
        vector_store,
        embed_model=embed_model,
    )
    return index


def query_documents(query: str, user_id: int, index: VectorStoreIndex) -> Response:
    """query vector db filtering based off user_id in metadata"""
    query_engine = index.as_query_engine(
        similarity_top_k=10,
        filters=MetadataFilters(
            filters=[
                MetadataFilter(
                    key="user_id",
                    value=user_id,
                )
            ]
        ),
    )
    pprint(query_engine.get_prompts())
    response = query_engine.query(query)
    return response


if __name__ == "__main__":
    from openai import AsyncOpenAI

    client = AsyncOpenAI()
    _logger.info("Loading documents...")
    context = SimpleDirectoryReader("../data").load_data()

    db = chromadb.PersistentClient(path=DB_PATH)
    chroma_collection = db.get_or_create_collection(
        COLLECTION, embedding_function=EMBED_MODEL
    )
    # query = "What diagnosis would explain my symptoms?"
    # context = get_context(
    #     query, 1, chroma_collection
    # )
    # organized_context = structure_context(context)
    # rqt = OAIRequest(
    #     system_msg=CHAT_W_DATA_SYS_MSG,
    #     user_msg=CHAT_W_DATA_USER_MSG.format(
    #         query, organized_context
    #     ),
    # )
    # response = asyncio.run(a_send_rqt_chat(client, rqt))
    # pprint(response)
