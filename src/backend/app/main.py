import logging
import os

import yaml
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api_v1.router import api_router

load_dotenv()

config_path = os.getenv(
    "LOGGING_CONFIG_PATH", "src/backend/app/utils/logging_config.yaml"
)


with open(config_path, "r") as config_file:
    logging_config = yaml.safe_load(config_file)

logging.config.dictConfig(logging_config)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Wilson AI API",
    description="""A FastAPI application to extract information from patient
    medical documents""",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
