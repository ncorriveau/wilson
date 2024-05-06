import logging
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from ...db.relational_db import authenticate_user, create_connection, get_db
from ...security.auth import create_access_token

logger = logging.getLogger(__name__)

router = APIRouter()

conn = create_connection()


@router.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = authenticate_user(conn, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(
        user["email"], expires_delta=timedelta(minutes=30)
    )
    return {"access_token": access_token, "userId": user["id"], "token_type": "bearer"}
