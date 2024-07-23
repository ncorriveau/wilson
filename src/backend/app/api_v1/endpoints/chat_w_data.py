import io
import logging

import chromadb
from fastapi import APIRouter, File, Header, HTTPException, UploadFile
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from PyPDF2 import PdfReader

from ...db.vector_db import (
    COLLECTION,
    DB_PATH,
    EMBED_MODEL,
    get_context,
    structure_context,
)
from ...deps import get_current_user
from ...models.open_ai.utils import OAIRequest, a_send_rqt

logger = logging.getLogger(__name__)

CHAT_W_DATA_SYS_MSG = """You are a word class medical physician who is also an expert in Q&A and you will assist in analyzing this patient's medical records
and responding to their questions to the best of your ability. For each query, you will be provided with the most relevant context
from the patients medical records. Additionally, piece of context will have information about the date of the appointment and the provider's name.
Please do not start talking about the users appointment data unless they ask questions about it or require the 
context of their appointments."""

CHAT_W_DATA_USER_MSG = """Based on the following context, please answer the 
query to the best of your ability. 
Please note that the context will contain metadata about the date of the appointment and the provider's name.
If the provider name and date are the same, you can assume it is from the same appointment. 
Query: {}
Context: {}
"""


class QueryRqt(BaseModel):
    query: str = Field(..., description="Query to be executed on the data")


# TODO: add back in auth when we figure out auth in the front end.
router = APIRouter()
client = AsyncOpenAI()
db = chromadb.PersistentClient(path=DB_PATH)
collection = db.get_or_create_collection(COLLECTION, embedding_function=EMBED_MODEL)


@router.post("/{user_id}")
async def query_data(user_id: int, query_rqt: QueryRqt):
    logger.info(f"Querying data for user {user_id} with query: {query_rqt.query}")
    context = get_context(query_rqt.query, user_id, collection)
    structured_context = structure_context(context)
    rqt = OAIRequest(
        system_msg=CHAT_W_DATA_SYS_MSG,
        user_msg=CHAT_W_DATA_USER_MSG.format(query_rqt.query, structured_context),
    )
    response = await a_send_rqt(client, rqt, response_json=False)
    return response


@router.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...), x_user_id: str = Header(...)):
    if not file.content_type == "application/pdf":
        raise HTTPException(
            status_code=400, detail="Invalid file type. Please upload a PDF."
        )
    content = await file.read()
    file_ = io.BytesIO(content)
    pdf_reader = PdfReader(file_)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()

    return {"filename": file.filename, "user_id": x_user_id}
