from fastapi import APIRouter, Depends, FastAPI

from .endpoints import appointments, chat_w_data, follow_ups, login, prescriptions

api_router = APIRouter()
api_router.include_router(
    appointments.router, prefix="/appointments", tags=["appointments"]
)
api_router.include_router(follow_ups.router, prefix="/follow_ups", tags=["follow_ups"])
api_router.include_router(
    chat_w_data.router, prefix="/chat_w_data", tags=["chat with data"]
)
api_router.include_router(login.router, prefix="/auth", tags=["login"])
api_router.include_router(
    prescriptions.router, prefix="/prescriptions", tags=["prescriptions"]
)
