import json
import os
from typing import Any, Dict, List

import psycopg2

password = os.getenv("POSTGRES_PASSWORD")

CREATE_TABLE_QUERY = """
CREATE TABLE IF NOT EXISTS appointment (
    id SERIAL PRIMARY KEY,
    filename TEXT NOT NULL,
    summary TEXT
    provider_name TEXT,
    appointment_date DATE,
    follow_ups JSONB,
    perscriptions JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);"""

INSERT_APPOINTMENT_QUERY = """
INSERT INTO appointment (filename, summary, physician, appointment_date, follow_ups, perscriptions)
VALUES (%s, %s, %s, %s, %s, %s)
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
