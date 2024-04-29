import logging

import yaml
from dotenv import load_dotenv
from fastapi import FastAPI

from .api_v1.router import api_router

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

app.include_router(api_router, prefix="/api/v1")
