import asyncio
import logging
import sys
from pprint import pprint
from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from openai import AsyncOpenAI, OpenAI
from psycopg2.extensions import connection
from pydantic import BaseModel, Field
from pymongo import MongoClient
from pymongo.collection import Collection

from ...db.nosql_db import get_provider_by_npi
from ...db.relational_db import (
    create_connection,
    get_prescriptions_by_id,
    set_prescription_status,
)
from ...deps import get_current_user
from .appointments import FollowUps, SpecialtyEnum, specialties

logger = logging.getLogger(__name__)


class ProviderInfo(BaseModel):
    firstName: str = Field(
        ..., description="The id of the provider.", alias="first_name"
    )
    lastName: str = Field(
        ..., description="The name of the provider.", alias="last_name"
    )
    specialty: SpecialtyEnum = Field(..., description="The specialty of the provider.")  # type: ignore


class PrescriptionResponse(BaseModel):
    id: int = Field(..., description="The id of the prescription.")
    brandName: str = Field(
        ..., description="The brand name of the prescription.", alias="brand_name"
    )
    technicalName: str = Field(
        ...,
        description="The technical name of the prescription.",
        alias="technical_name",
    )
    instructions: str = Field(..., description="The instructions for the prescription.")
    providerInfo: ProviderInfo = Field(
        ...,
        description="The provider information for the prescription.",
        alias="provider_info",
    )
    isActive: bool = Field(
        ..., description="The active status of the prescription.", alias="active_flag"
    )

    class Config:
        allow_population_by_field_name = True


def get_prescriptions(
    user_id: int, conn: connection, collection: Collection
) -> List[PrescriptionResponse]:
    prescriptions = get_prescriptions_by_id(conn, user_id)
    prescription_models = []
    for prescription in prescriptions:
        provider_info = get_provider_by_npi(collection, prescription["provider_id"])
        return_provider_info = {
            "first_name": provider_info["first_name"],
            "last_name": provider_info["last_name"],
            "specialty": provider_info["specialties"][0],
        }
        prescription["provider_info"] = return_provider_info
        prescription.pop("provider_id")
        prescription_models.append(PrescriptionResponse(**prescription))

    return prescription_models


# dependencies=[Depends(get_current_user)]
router = APIRouter()

mongo_db_client = MongoClient("mongodb://localhost:27017/")
db = mongo_db_client["wilson_ai"]
conn = create_connection()
provider_collection = db.providers


@router.get("/{user_id}")
async def prescriptions(user_id: int):
    prescriptions = get_prescriptions(user_id, conn, provider_collection)
    return [prescription.model_dump(by_alias=False) for prescription in prescriptions]


@router.put("/status/{prescription_id}")
async def set_status(prescription_id: int, prescription: Dict[str, Any]):
    print(prescription)
    set_prescription_status(conn, prescription_id, prescription["isActive"])
    return JSONResponse(
        status_code=200, content={"message": "Prescription status updated"}
    )


if __name__ == "__main__":
    client_db = MongoClient("mongodb://localhost:27017/")
    db = client_db["wilson_ai"]
    collection = db.providers
    conn = create_connection()

    prescriptions = get_prescriptions(1, conn, collection)
    pprint(prescriptions)
