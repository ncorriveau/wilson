import io

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile
from pydantic import BaseModel, Field
from PyPDF2 import PdfReader

from ...db.vector_db import build_index, embed_model_llamaindex, query_documents
from ...deps import get_current_user


class QueryRqt(BaseModel):
    query: str = Field(..., description="Query to be executed on the data")


# TODO: add back in auth when we figure out auth in the front end.
router = APIRouter()


@router.post("/{user_id}")
async def query_data(user_id: int, query_rqt: QueryRqt):
    index = build_index(embed_model_llamaindex)
    response = query_documents(query_rqt.query, user_id, index)
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
