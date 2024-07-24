import logging
import os
from pprint import pprint
from typing import List

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from psycopg2.extensions import connection
from pymongo import MongoClient
from pymongo.collection import Collection

from ...db.nosql_db import get_provider_by_npi
from ...db.relational_db import (
    create_connection,
    get_prescriptions_by_id,
    set_prescription_status,
)
from ...pydantic_models.pyd_models import PrescriptionRequest, PrescriptionResponse

logger = logging.getLogger(__name__)

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")


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
mongo_db_client = MongoClient(MONGODB_URL)
db = mongo_db_client["wilson_ai"]
conn = create_connection()
provider_collection = db.providers


@router.get("/{user_id}")
async def prescriptions(user_id: int):
    prescriptions = get_prescriptions(user_id, conn, provider_collection)
    return [prescription.model_dump(by_alias=False) for prescription in prescriptions]


@router.put("/status/{prescription_id}")
async def set_status(prescription_id: int, rqt: PrescriptionRequest):
    set_prescription_status(conn, prescription_id, rqt.active_flag)
    return JSONResponse(
        status_code=200, content={"message": "Prescription status updated"}
    )


if __name__ == "__main__":
    client_db = MongoClient(MONGODB_URL)
    db = client_db["wilson_ai"]
    collection = db.providers
    conn = create_connection()

    prescriptions = get_prescriptions(1, conn, collection)
    pprint(prescriptions)
