from llama_parse import LlamaParse
import os.path
import logging
import chromadb  
import sys
import click
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
)
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

PERSIST_DIR = "./storage"

def init_store(data_path: str, storage_path: str):
    # check if storage already exists
    if not os.path.exists(storage_path):
        # load the documents and create the index
        documents = SimpleDirectoryReader(data_path).load_data()
        index = VectorStoreIndex.from_documents(documents)
        index.storage_context.persist(persist_dir=storage_path)
    else:
        # load the existing index
        storage_context = StorageContext.from_defaults(persist_dir=storage_path)
        index = load_index_from_storage(storage_context)
    
    return index 


@click.command()
@click.option('--question', prompt='Your question', required=True)
def ask_question(question: str)-> None:
    index = init_store("./data", PERSIST_DIR)
    query_engine = index.as_query_engine()
    response = query_engine.query(question)
    print(response)

if __name__ == "__main__":
    ask_question()
    # if not os.path.exists(PERSIST_DIR):
    #     documents = SimpleDirectoryReader("data").load_data()
    #     index = VectorStoreIndex.from_documents(documents)
    #     # store it for later
    #     # don't have to ask openai for embeddings each rqt now 
    #     index.storage_context.persist(persist_dir=PERSIST_DIR)
    # else:
    #     storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
    #     index = load_index_from_storage(storage_context)
# def main():
#     parser = LlamaParse(
#     result_type="markdown",
#     verbose=True,
#     language="en",
#     num_workers=2,
#     )
#     document = parser.loda_data("data/llama_index_data.txt")
#     print(document)

# if __name__ == "__main__":
#     main()
    
