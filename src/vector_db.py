"""Functions to aid in the indexing and storing of data in a vector database """

import logging
import os
from typing import Any, Dict

import chromadb
from IPython.display import Markdown, display
from llama_index.core import SimpleDirectoryReader, StorageContext, VectorStoreIndex
from llama_index.core.base.response.schema import Response
from llama_index.core.schema import MetadataMode
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

_logger = logging.getLogger(__name__)

os.environ["TOKENIZERS_PARALLELISM"] = "false"

COLLECTION = "appointment"
DB_PATH = "./chroma_db"

embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-base-en-v1.5")


# load documents
# meta data something like user id, document name, appointment visit time, etc
def load_documents(data_path: str, metadata: Dict[Any, Any]) -> None:
    """Load documents from a directory into the vector database."""
    documents = SimpleDirectoryReader(data_path).load_data()
    for document in documents:
        document.metadata = metadata

    _logger.debug(
        "The LLM sees this: %s\n",
        document.get_content(metadata_mode=MetadataMode.LLM),
    )
    _logger.debug(
        "The Embedding model sees this: %s\n",
        document.get_content(metadata_mode=MetadataMode.EMBED),
    )

    db = chromadb.PersistentClient(path=DB_PATH)
    chroma_collection = db.get_or_create_collection(COLLECTION)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    VectorStoreIndex.from_documents(
        documents, storage_context=storage_context, embed_model=embed_model
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


def query_documents(query: str, index) -> Response:
    query_engine = index.as_query_engine()
    response = query_engine.query(query)
    return response


if __name__ == "__main__":
    _logger.info("Loading documents...")
    load_documents("../data", {"filename": "appointment1"})

    _logger.info("Building index...")
    index = build_index(embed_model)

    _logger.info("Querying documents...")
    response = query_documents("What is the patient's name?", index)
    print(response)
