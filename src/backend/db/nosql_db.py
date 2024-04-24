from bson.objectid import ObjectId
from pymongo import MongoClient

from ..app.appointments import ProviderInfo

# Establish connection
client = MongoClient("mongodb://localhost:27017/")
db = client["wilson_ai"]
providers = db.providers

# Example document
provider_info = {
    "first_name": "Ella",
    "last_name": "Leers",
    "degree": "MD",
    "email": None,
    "phone_number": None,
    "npi": "1609958305",
    "specialty": "PCP",
    "locations": [
        {
            "name": "One Medical",
            "street": "5 Columbus Circle Suite 1802",
            "city": "New York",
            "state": "NY",
            "zip_code": "10019",
            "coordinates": {
                "lat": None,
                "long": None,
            },
        },
    ],
    "insurance": [],
}

# Inserting a document
inserted_id = providers.insert_one(provider_info).inserted_id
print("Inserted physician with ID:", inserted_id)

# Fetching a document
doc = providers.find_one({"_id": ObjectId(inserted_id)})
print(doc)

# Updating a document
providers.update_one(
    {"_id": ObjectId(inserted_id)}, {"$set": {"specialty": "Dermatology"}}
)
updated_doc = providers.find_one({"_id": ObjectId(inserted_id)})
print(updated_doc)

# Deleting a document
providers.delete_one({"_id": ObjectId(inserted_id)})
print(f"Deleted physician with ID: {inserted_id}")
