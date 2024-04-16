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

CREATE_LOCATION_QUERY = """
CREATE TABLE IF NOT EXISTS location (
    id SERIAL PRIMARY KEY,
    street TEXT NOT NULL,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    zip_code TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);"""

INSERT_INTO_LOCATION_QUERY = """
INSERT INTO location (street, city, state, zip_code)
VALUES (%(street)s, %(city)s, %(state)s, %(zip_code)s)
"""


INSERT_APPOINTMENT_QUERY = """
INSERT INTO appointment (user_id, provider_id, filename, summary, appointment_date, follow_ups, perscriptions)
VALUES (%(user_id)s, %(provider_id)s, %(filename)s, %(summary)s, %(appointment_date)s, %(follow_ups)s, %(perscriptions)s)
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
INSERT INTO providers (first_name, last_name, degree, email, npi, specialty_id, location_id)
VALUES (%(first_name)s, %(last_name)s, %(degree)s, %(email)s, %(npi)s, %(specialty_id)s, %(location_id)s)
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
    description TEXT,
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
    CREATE_LOCATION_QUERY,
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


def insert_location(conn: connection, params: Dict[str, str]) -> None:
    insert_row(conn, INSERT_APPOINTMENT_QUERY, params)


def insert_provider(conn: connection, params: Dict[str, str]) -> None:
    insert_row(conn, INSERT_PROVIDER_QUERY, params)


def query_db(
    conn: connection, query: str, params: Dict[str, str] = None
) -> List[Dict[str, Any]]:
    """
    Generic helper function to execute queries on the database
    """
    cursor = conn.cursor()
    try:
        if not params:
            cursor.execute(query)
        else:
            cursor.execute(query, params)
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


def get_specialties(conn: connection) -> Dict[str, str]:
    query = "SELECT specialty, description FROM specialties"
    results = query_db(conn, query)
    specialties = {result[0]: result[1] for result in results}
    return specialties


def get_specialty_id(conn: connection, specialty: str) -> Dict[str, str]:
    query = f"SELECT specialty_id FROM specialties where specialty = {specialty}"
    results = query_db(conn, query)
    return results[0][0]


def get_location_id(conn: connection, location_params: Dict[str, str]) -> int:
    query = """
    SELECT id FROM location 
    WHERE street = %(street)s AND 
    city = %(city)s AND 
    state = %(state)s AND 
    zip_code = %(zip_code)s"""

    results = query_db(conn, query, location_params)
    return results[0][0]


def get_provider_id_by_npi(conn: connection, npi: str) -> int:
    query = f"SELECT id FROM providers WHERE npi = {npi}"
    results = query_db(conn, query)
    return results[0][0]


def get_provider_id(
    conn: connection,
    first_name: str,
    last_name: str,
    degree: str,
    optional_params: Dict[str, Any],
) -> int:
    # THIS FUNCTION NEEDS TO BE REWORKED
    # WE DO NOT HANDLE THE CASE WHERE WE HAVE SOME INFO AND WE GAIN INFO FROM THE UPLOAD
    # (e.g. we now have an address where we didn't have before)
    # IN WHICH CASE WE WOULD LIKE TO UPDATE EXISTING ENTRY VS CREATING A NEW ONE

    query = f"""
    SELECT id FROM providers 
    WHERE first_name = {first_name} AND 
    last_name = {last_name}"""

    if npi := optional_params.get("npi"):
        query += f""" AND npi = {npi}"""
    if phone_number := optional_params.get("phone_number"):
        query += f""" AND phone_number = {phone_number}"""
    if email := optional_params.get("email"):
        query += f""" AND email = {email}"""
    if location_id := optional_params.get("location_id"):
        query += f""" AND location_id = {location_id}"""
    if specialty_id := optional_params.get("specialty_id"):
        query += f""" AND specialty_id = {specialty_id}"""

    if address := optional_params.get("address"):
        location_id = get_location_id(conn, optional_params.get("address"))
        if location_id:
            query += f""" AND location_id = {location_id}"""
    if specialty := optional_params.get("specialty"):
        specialty_id = get_specialty_id(conn, optional_params.get("specialty"))
        if specialty_id:
            query += f""" AND specialty_id = {specialty_id}"""

    results = query_db(conn, query)
    return results[0][0]


if __name__ == "__main__":
    appointtment_meta = {
        "AppointmentMeta": {
            "provider_info": {
                "first_name": "Ella",
                "last_name": "Leers",
                "degree": "MD",
                "email": None,
                "phone_number": None,
                "npi": "1609958305",
                "address": {
                    "street": "5 Columbus Circle Suite 1802",
                    "city": "New York",
                    "state": "NY",
                    "zip_code": "10019",
                },
                "specialty": "PCP",
            },
            "date": "2023-09-12",
        },
    }

    # conn = create_connection()
    # # async def main():
    # #     async with asyncpg.create_pool(**async_pg_params) as pool:
    # #         async with pool.acquire() as conn:
    # #             print(f"Executing statement")
    # #             await conn.execute(CREATE_APPT_TABLE_QUERY)

    # # asyncio.run(main())
    # print(get_specialties(conn))
    # # create_table(
    # #     conn,
    # #     [CREATE_SPECIALTIES_QUERY],
    # #     # [
    # #     #     CREATE_APPT_TABLE_QUERY,
    # #     #     # CREATE_COVERAGE_TYPE_QUERY,
    # #     #     # CREATE_INSURANCE_QUERY,
    # #     #     # CREATE_USER_QUERY,
    # #     #     # CREATE_PROVIDER_QUERY,
    # #     #     # CREATE_PERSCRIPTION_QUERY,
    # #     #     # CREATE_PROVIDER_TO_INSURANCE_QUERY,
    # #     #     # CREATE_USER_TO_INSURANCE_QUERY,
    # #     # ],
    # # )
    # # print(f"Table created successfully")
    # conn.close()
