from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from psycopg2.extensions import connection
from pydantic import BaseModel

from .db.relational_db import create_connection, get_db, get_user_by_email
from .security.auth import verify_token

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/token")


class TokenData(BaseModel):
    username: str | None = None


TokenDep = Annotated[str, Depends(reusable_oauth2)]

conn = create_connection()


async def get_current_user(token: Annotated[str, Depends(reusable_oauth2)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = verify_token(token, credentials_exception)

    # username passed in log in is email
    user = get_user_by_email(conn, email=payload.get("sub"))
    print(user)
    if user is None:
        raise credentials_exception
    return user
