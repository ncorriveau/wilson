import hashlib
import json
import os
from enum import Enum
from typing import Any, Dict

import yaml
from dotenv import load_dotenv

load_dotenv()

config_path = os.getenv("CONFIG_PATH", "src/backend/app/utils/config.yaml")


class Env(Enum):
    PRODUCTION = "PROD"
    QA = "QA"
    DEV = "DEV"


def get_environment() -> Env:
    """Get the current environment."""
    env = os.environ.get("ENV")
    try:
        return Env(env)
    except:
        raise ValueError(f"Invalid environment: {env}. Expected one of: {list(Env)}")


def read_config(env: Env) -> Dict[str, Any]:
    """Read the configuration file."""
    if env not in Env:
        raise ValueError(f"Invalid environment: {env}. Expected one of: {list(Env)}")
    with open(config_path, "r") as config_file:
        config = yaml.safe_load(config_file)
    return config[env.value]


def construct_redis_url(config: Dict[str, Any]) -> str:
    """Construct the Redis URL from the configuration."""
    return f"redis://{config['redis']['host']}"


def construct_mongo_url(config: Dict[str, Any]) -> str:
    """Construct the MongoDB URL from the configuration."""
    return f"mongodb://{config['mongo']['host']}:{config['mongo']['port']}"


def get_locations() -> Dict[str, str]:
    """Get the locations from the configuration."""
    config = read_config(get_environment())
    return {
        "mongo_db": construct_mongo_url(config),
        "redis": construct_redis_url(config),
    }


def create_hash_id(context: str, metadata: Dict[str, str]) -> str:
    """Create unique hash id for document + meta data to use as document id."""
    json_string = json.dumps(metadata) + context

    # Create a SHA256 hash object
    hash_object = hashlib.sha256()
    hash_object.update(json_string.encode())
    hash_hex = hash_object.hexdigest()

    return hash_hex


if __name__ == "__main__":
    env = get_environment()
    print(env)

    config = read_config(env)
    redis_url = construct_redis_url(config)
    mongo_url = construct_mongo_url(config)

    print(f"Redis URL: {redis_url}")
    print(f"MongoDB URL: {mongo_url}")
