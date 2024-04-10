"""Functions to aid in the indexing and storing of data in a vector database """

import hashlib
import json
import logging
import os
from typing import Any, Dict, List

import chromadb
import chromadb.utils.embedding_functions as embedding_functions
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.base.response.schema import Response
from llama_index.core.schema import Document
from llama_index.core.vector_stores import MetadataFilter, MetadataFilters
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

_logger = logging.getLogger(__name__)

os.environ["TOKENIZERS_PARALLELISM"] = "false"

COLLECTION = "appointment"
DB_PATH = "/Users/nickocorriveau/dev/wilson/chroma_db"
HF_EMBED_MODEL = "BAAI/bge-base-en-v1.5"

embed_model_llamaindex = HuggingFaceEmbedding(model_name=HF_EMBED_MODEL)
embed_model_chroma = embedding_functions.HuggingFaceEmbeddingFunction(
    api_key=os.environ["HUGGINGFACE_API_KEY"],
    model_name=HF_EMBED_MODEL,
)


def create_hash_id(context: str, metadata: Dict[str, str]) -> str:
    """Create unique hash id for document + meta data to use as document id."""
    json_string = json.dumps(metadata) + context

    # Create a SHA256 hash object
    hash_object = hashlib.sha256()
    hash_object.update(json_string.encode())
    hash_hex = hash_object.hexdigest()

    return hash_hex


def load_documents(documents: List[Document], metadata: Dict[Any, Any]) -> None:
    """Load documents from a directory into the vector database."""
    client = chromadb.PersistentClient(path=DB_PATH)
    collection = client.get_or_create_collection(
        name=COLLECTION, embedding_function=embed_model_chroma
    )

    collection.upsert(
        documents=[document.text for document in documents],
        metadatas=[metadata for _ in documents],
        ids=[create_hash_id(document.text, metadata) for document in documents],
    )
    return


def build_index(embed_model: Any) -> VectorStoreIndex:
    db = chromadb.PersistentClient(path=DB_PATH)
    chroma_collection = db.get_or_create_collection(COLLECTION)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    index = VectorStoreIndex.from_vector_store(
        vector_store,
        embed_model=embed_model,
    )
    return index


def query_documents(query: str, user_id: int, index) -> Response:
    """query vector db filtering based off user_id in metadata"""
    query_engine = index.as_query_engine(
        filters=MetadataFilters(
            filters=[
                MetadataFilter(
                    key="user_id",
                    value=user_id,
                )
            ]
        )
    )
    response = query_engine.query(query)
    return response


if __name__ == "__main__":
    _logger.info("Loading documents...")
    context = SimpleDirectoryReader("data").load_data()
    load_documents(context, {"filename": "appointment1"})

    _logger.info("Building index...")
    index = build_index(embed_model_llamaindex)

    _logger.info("Querying documents...")
    response = query_documents("What is the patient's name?", 1, index)

    print(response)