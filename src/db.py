import json
import os
from typing import Any, Dict, List

import psycopg2

password = os.getenv("POSTGRES_PASSWORD")

CREATE_TABLE_QUERY = """
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

INSERT_APPOINTMENT_QUERY = """
INSERT INTO appointment (filename, summary, provider_name, appointment_date, follow_ups, perscriptions)
VALUES (%s, %s, %s, %s, %s, %s)
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
    email TEXT,
    specialty TEXT,
    location TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""
INSERT_PROVIDER_QUERY = """
INSERT INTO providers (first_name, last_name, email, specialty, location)
VALUES (%s, %s, %s, %s, %s)
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


# TODO: read these from config
def create_connection():
    conn = psycopg2.connect(
        dbname="postgres",
        user="postgres",
        password=password,
        host="localhost",
        port="5432",
    )
    return conn


def create_table(conn, create_queries: List[str]) -> None:
    cursor = conn.cursor()
    for query in create_queries:
        cursor.execute(query)
    conn.commit()
    cursor.close()


def insert_appointment(conn, params: Dict[str, str]) -> None:
    cursor = conn.cursor()
    try:
        cursor.execute(
            INSERT_APPOINTMENT_QUERY,
            (
                params.get("filename"),
                params.get("summary"),
                params.get("provider_name"),
                params.get("appointment_date"),
                params.get("follow_ups"),
                params.get("perscriptions"),
            ),
        )
        conn.commit()

    except Exception as e:
        print(e)
        conn.rollback()

    finally:
        cursor.close()


if __name__ == "__main__":
    conn = create_connection()
    create_table(
        conn,
        [
            CREATE_TABLE_QUERY,
            CREATE_USER_QUERY,
            CREATE_PROVIDER_QUERY,
            CREATE_PERSCRIPTION_QUERY,
            CREATE_INSURANCE_QUERY,
            CREATE_PROVIDER_TO_INSURANCE_QUERY,
            CREATE_USER_TO_INSURANCE_QUERY,
        ],
    )
    conn.close()
    print("TABLES CREATED")
