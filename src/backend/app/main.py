import logging

import yaml
from dotenv import load_dotenv
from fastapi import Depends, FastAPI

from .api_v1.endpoints import appointments, chat_w_data, follow_ups, login
from .deps import get_current_user

load_dotenv()

with open(
    "/Users/nickocorriveau/dev/wilson/src/backend/app/configs/logging_config.yaml", "r"
) as config_file:
    logging_config = yaml.safe_load(config_file)

logging.config.dictConfig(logging_config)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Wilson AI API",
    description="""A FastAPI application to extract information from patient
    medical documents""",
    version="0.1.0",
)

app.include_router(appointments.router, prefix="/appointments", tags=["appointments"])
app.include_router(follow_ups.router, prefix="/follow_ups", tags=["follow_ups"])
app.include_router(chat_w_data.router, prefix="/chat_w_data", tags=["chat with data"])
app.include_router(login.router, prefix="/auth", tags=["login"])


@app.get("/")
async def root():
    return {"message": "Welcome to Wilson AI API!"}
