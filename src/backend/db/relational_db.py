import asyncio
import json
import os
from typing import Any, Dict, List

import asyncpg
import psycopg2
from psycopg2.extensions import connection

password = os.getenv("POSTGRES_PASSWORD")

CREATE_APPT_TABLE_QUERY = """
CREATE TABLE IF NOT EXISTS appointment (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider_id INT NOT NULL REFERENCES providers(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    summary TEXT,
    appointment_date DATE,
    follow_ups JSONB,
    perscriptions JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);"""

CREATE_COVERAGE_TYPE_QUERY = """
CREATE TABLE IF NOT EXISTS coverage_type (
    id SERIAL PRIMARY KEY,
    type TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


CREATE_INSURANCE_QUERY = """
CREATE TABLE IF NOT EXISTS insurance (
    id SERIAL PRIMARY KEY,
    company_name TEXT NOT NULL,
    insurance_name TEXT NOT NULL,
    policy_number TEXT NOT NULL,
    coverage_type_id INT NOT NULL REFERENCES coverage_type(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


INSERT_APPOINTMENT_QUERY = """
INSERT INTO appointment (user_id, provider_id, filename, summary, appointment_date, follow_ups, perscriptions)
VALUES (%(user_id)s, %(provider_id)s, %(filename)s, %(summary)s, %(appointment_date)s, %(follow)ups)s, %(perscriptions)s)
"""

CREATE_USER_QUERY = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL,
    insurance_id INT NOT NULL REFERENCES insurance(id),
    birthdate DATE NOT NULL,
    location TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

INSERT_INTO_USER_QUERY = """
INSERT INTO users (first_name, last_name, email, insurance_id, birthdate, location)
VALUES (%s, %s, %s, %s, %s, %s)
"""

CREATE_PROVIDER_QUERY = """
CREATE TABLE IF NOT EXISTS providers (
    id SERIAL PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    specialty_id INT NOT NULL REFERENCES specialties(id),
    email TEXT,
    location TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""
INSERT_PROVIDER_QUERY = """
INSERT INTO providers (first_name, last_name, email, specialty, location)
VALUES (%(first_name)s, %(last_name)s, %(email)s, %(specialty)s, %(location)s)
"""

CREATE_PERSCRIPTION_QUERY = """
CREATE TABLE IF NOT EXISTS perscriptions (
    id SERIAL PRIMARY KEY,
    brand_name TEXT NOT NULL,
    technical_name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

INSERT_PERSCRIPTION_QUERY = """
INSERT INTO perscriptions (brand_name, technical_name)
VALUES (%s, %s)
"""

CREATE_PROVIDER_TO_INSURANCE_QUERY = """
CREATE TABLE IF NOT EXISTS provider_to_insurance (
    id SERIAL PRIMARY KEY,
    provider_id INT NOT NULL REFERENCES providers(id),
    insurance_id INT NOT NULL REFERENCES insurance(id),
    start_date DATE NOT NULL,
    end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_USER_TO_INSURANCE_QUERY = """
CREATE TABLE IF NOT EXISTS user_to_insurance (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id),
    insurance_id INT NOT NULL REFERENCES insurance(id),
    start_date DATE NOT NULL,
    end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_SPECIALTIES_QUERY = """
CREATE TABLE IF NOT EXISTS specialties (
    id SERIAL PRIMARY KEY,
    specialty VARCHAR(255) UNIQUE NOT NULL,
    friendly_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

pg_params = {
    "dbname": "postgres",
    "user": "postgres",
    "password": password,
    "host": "localhost",
    "port": "5432",
}

async_pg_params = {
    "database": "postgres",
    "user": "postgres",
    "password": password,
    "host": "localhost",
    "port": "5432",
}


CREATE_QUERIES = [
    CREATE_APPT_TABLE_QUERY,
    CREATE_COVERAGE_TYPE_QUERY,
    CREATE_INSURANCE_QUERY,
    CREATE_USER_QUERY,
    CREATE_PROVIDER_QUERY,
    CREATE_PERSCRIPTION_QUERY,
    CREATE_PROVIDER_TO_INSURANCE_QUERY,
    CREATE_USER_TO_INSURANCE_QUERY,
    CREATE_SPECIALTIES_QUERY,
]


async def create_pool():
    return await asyncpg.create_pool(
        **async_pg_params,
    )


# TODO: read these from config
def create_connection() -> connection:
    conn = psycopg2.connect(**pg_params)
    return conn


def create_table(conn: connection, create_queries: List[str]) -> None:
    cursor = conn.cursor()
    for query in create_queries:
        print(f"executing query: {query}")
        cursor.execute(query)
        print(f"Query executed")
        conn.commit()
    cursor.close()


def insert_appointment(conn: connection, params: Dict[str, str]) -> None:
    insert_row(conn, INSERT_APPOINTMENT_QUERY, params)


def query_db(conn: connection, query: str) -> List[Dict[str, Any]]:
    """
    Generic helper function to execute queries on the database
    """
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        result = cursor.fetchall()

    except Exception as e:
        result = f"Error while executing query {e}"

    return result


def insert_row(conn: connection, query: str, params: Dict[str, str]) -> None:
    """
    Helper function to insert rows into a table. Assumes the query is formatted
    with named arguments.
    """
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        conn.commit()

    except Exception as e:
        print(f"Error while inserting data into table {e}")
        conn.rollback()
        raise e


if __name__ == "__main__":
    conn = create_connection()
    # async def main():
    #     async with asyncpg.create_pool(**async_pg_params) as pool:
    #         async with pool.acquire() as conn:
    #             print(f"Executing statement")
    #             await conn.execute(CREATE_APPT_TABLE_QUERY)

    # asyncio.run(main())

    create_table(
        conn,
        [CREATE_SPECIALTIES_QUERY],
        # [
        #     CREATE_APPT_TABLE_QUERY,
        #     # CREATE_COVERAGE_TYPE_QUERY,
        #     # CREATE_INSURANCE_QUERY,
        #     # CREATE_USER_QUERY,
        #     # CREATE_PROVIDER_QUERY,
        #     # CREATE_PERSCRIPTION_QUERY,
        #     # CREATE_PROVIDER_TO_INSURANCE_QUERY,
        #     # CREATE_USER_TO_INSURANCE_QUERY,
        # ],
    )
    print(f"Table created successfully")
    conn.close()
