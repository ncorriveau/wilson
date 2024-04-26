import logging
import pprint
from typing import Any, Dict

import requests
from bson.objectid import ObjectId
from pymongo import MongoClient
from pymongo.collection import Collection, UpdateResult

from .relational_db import geocode_address

SUGGESTION_MAX_DISTANCE = 10000  # distance in meters
NPI_URL = "https://npiregistry.cms.hhs.gov/api/?version=2.1"

logger = logging.getLogger(__name__)

# TODO: we need to add specialty in our queries sand have a map from our db to the npi db for taxonomies


def get_npi(provider_info: Dict[str, any]) -> str:
    """given a providers name / specialty / etc pull npi from the npi database"""

    # if we don't have a location there will still be a location attribute
    # it will just be none
    if location := provider_info["location"]:
        city = location.get("city")
        state = location.get("state")
    else:
        city = None
        state = None

    # structure request to npi database
    params_list = [
        {
            "first_name": provider_info.get("first_name"),
            "last_name": provider_info.get("last_name"),
            "city": city,
            "state": state,
        },
        {
            "first_name": provider_info.get("first_name"),
            "last_name": provider_info.get("last_name"),
            "state": state,
        },
        {
            "first_name": provider_info.get("first_name"),
            "last_name": provider_info.get("last_name"),
        },
    ]
    for params in params_list:
        response = requests.get(NPI_URL, params=params)
        if response.json()["results"]:
            # TODO figure out how we want to handle multiple results
            return response.json()["results"][0]["number"]

    return None


def get_provider_by_npi(collection: Collection, npi: str) -> Dict[str, Any]:
    return collection.find_one({"npi": npi})


def upsert_provider(
    collection: Collection, provider_info: Dict[str, Any]
) -> UpdateResult:
    """insert or update provider info in db"""
    if provider_info["location"]:
        lat, lng = geocode_address(provider_info["location"])
        provider_info["location"]["coordinates"] = {"lat": lat, "long": lng}

    result = collection.update_one(
        {"npi": provider_info["npi"]},
        {
            "$set": {
                "first_name": provider_info["first_name"],
                "last_name": provider_info["last_name"],
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
    logger.info(f"Upserted provider: {provider_info['npi']}")
    return result


async def get_provider_id(collection: Collection, provider_info: Dict[str, Any]) -> str:
    """
    This function implements a waterfall logic in order to try and locate
    the npi based on provider info.
        1) If the npi is not present, try to find the provider in the db
        based on first name, last name, and specialty
        2) If the provider is not found in the db, query the npi db to get the npi
            If we successfully find one, we want to insert the provider into the db
        else will return None.
    Future work may include handing multiple results to an llm to decide which one
    to suggest to the user and have user confirm.
    """
    provider = collection.find_one(
        {
            "first_name": provider_info["first_name"],
            "last_name": provider_info["last_name"],
            "specialties": provider_info["specialty"],
        }
    )

    # TODO: if there are multiple matches, maybe we should return all of them and ask the user to pick one
    if provider:
        logger.info(f"Found provider in db: {provider['npi']}")
        return provider["npi"]

    logger.info(
        f"Querying npi db for provider: {provider_info['first_name']} {provider_info['last_name']}"
    )
    provider_info["npi"] = get_npi(provider_info)
    return provider_info["npi"]


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
    return list(results)


if __name__ == "__main__":

    # Establish connection
    client = MongoClient("mongodb://localhost:27017/")
    db = client["wilson_ai"]
    providers = db.providers

    # Example document that will come in
    # note that the document 'schema' will contain a list of locations and insurances but on any given
    # update we will just be providing one from the incoming document
    provider_info = {
        # "npi": "1447331368",
        "first_name": "Christine",
        "last_name": "Corriveau",
        "degree": "MD",
        "email": None,
        "phone_number": None,
        "specialty": "PEDIATRIC",
        # more complex info
        "location": {
            "name": "Children's National Hospital",
            "street": "111 Michigan Ave NW",
            "city": "WASHINGTON",
            "state": "DC",
            "zip_code": "20010-2978",
            "coordinates": {
                "lat": 40.766668,
                "long": -73.9814608,
            },
        },
    }

    # # # Inserting a document
    # # inserted_id = providers.insert_one(provider_info).inserted_id
    # # print("Inserted physician with ID:", inserted_id)
    # modified_count = upsert_provider(providers, provider_info)

    patient_info = {"lat": 40.766668, "lng": -73.9814608, "insurance_id": 3}

    # # Fetching a document
    # # doc = providers.find_one({"specialties": 'PCP', "insurances.id": patient_info["insurance_id"]})  # , "insurances.insurance_id": patient_info["insurance_id"]
    # # pprint.pprint(doc)
    results = get_relevant_providers(providers, patient_info, "PCP")
    print(results)
    # for result in results:
    #     pprint.pprint(result)
    # results = get_provider_id(providers, provider_info)
    # doc = providers.find_one({"npi": "1609958305"})
    # for r in results:
    #     pprint.pprint(r)
