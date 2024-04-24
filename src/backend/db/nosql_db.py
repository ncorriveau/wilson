import pprint
from typing import Any, Dict

from bson.objectid import ObjectId
from pymongo import MongoClient
from pymongo.collection import Collection

# from ..app.appointments import ProviderInfo

SUGGESTION_MAX_DISTANCE = 10000  # distance in meters


def get_npi(provider_info: Dict[str, any]) -> str:
    """given a providers name / specialty / etc pull npi from the npi database"""

    # structure request to npi database

    # return npi if there is a single one

    pass


def get_provider_by_npi(collection: Collection, npi: str) -> Dict[str, Any]:
    return collection.find_one({"npi": npi})


def upsert_provider(collection: Collection, provider_info: Dict[str, Any]) -> int:
    """insert or update provider info in db"""
    result = collection.update_one(
        {"npi": provider_info["npi"]},
        {
            "$set": {
                "email": provider_info["email"],
                "phone_number": provider_info["phone_number"],
            },
            "$addToSet": {
                "locations": provider_info["location"],
                "specialties": provider_info["specialty"],
            },
        },
        upsert=True,
    )
    return result.modified_count


def get_relevant_providers(
    provider_collection: Collection, patient_info: Dict[str, any], specialty: str
):
    """
    for a given patient, return providers that are with in a certain distance, take
    the required insurance, and meet the required specialty

    Parameters
    ----------
    provider_collection : Collection
        The collection of providers
    patient_info : Dict[str, any]
        The information about the patient must contain lat, lng, and insurance_id
    specialty : str
        The specialty of the provider - enforced values can only be from what we have the specialty table
    """
    query = {
        "locations.coordinates": {
            "$near": {
                "$geometry": {
                    "type": "Point",
                    "coordinates": [patient_info["lat"], patient_info["lng"]],
                },
                "$maxDistance": SUGGESTION_MAX_DISTANCE,
            }
        },
        "specialties": specialty,
        "insurances.id": patient_info["insurance_id"],
    }
    # Perform the query
    results = provider_collection.find(query)
    return results


if __name__ == "__main__":

    # Establish connection
    client = MongoClient("mongodb://localhost:27017/")
    db = client["wilson_ai"]
    providers = db.providers

    # Example document that will come in
    # note that the document 'schema' will contain a list of locations and insurances but on any given
    # update we will just be providing one from the incoming document
    provider_info = {
        "npi": "1609958305",
        "first_name": "Ella",
        "last_name": "Leers",
        "degree": "MD",
        "email": None,
        "phone_number": None,
        "specialty": ["PCP"],
        # more complex info
        "location": {
            "name": "One Medical",
            "street": "5 Columbus Circle Suite 1802",
            "city": "New York",
            "state": "NY",
            "zip_code": "10019",
            "coordinates": {
                "lat": 40.766668,
                "long": -73.9814608,
            },
        },
    }

    # # Inserting a document
    # inserted_id = providers.insert_one(provider_info).inserted_id
    # print("Inserted physician with ID:", inserted_id)
    modified_count = upsert_provider(providers, provider_info)
    print(modified_count)
    patient_info = {"lat": 40.766668, "lng": -73.9814608, "insurance_id": 3}

    # Fetching a document
    # doc = providers.find_one({"specialties": 'PCP', "insurances.id": patient_info["insurance_id"]})  # , "insurances.insurance_id": patient_info["insurance_id"]
    # pprint.pprint(doc)
    results = get_relevant_providers(providers, patient_info, "PCP")
    for result in results:
        pprint.pprint(result)
