from fastapi import APIRouter, Depends, HTTPException

from ..db.relational_db import authenticate_user, get_db
from ..security.auth import create_access_token

router = APIRouter()


@router.post("/token")
async def login(username: str, password: str, db=Depends(get_db)):
    user = authenticate_user(db, username, password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user["email"]})
    return {"access_token": access_token, "token_type": "bearer"}
