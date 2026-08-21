"""Shared PostgresSaver checkpointer for LangGraph agents.

Uses its own psycopg connection pool, separate from the SQLAlchemy engine
in database.py.
"""
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool

from dotenv import load_dotenv
import os

load_dotenv()

DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')

CHECKPOINTER_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

connection_pool = ConnectionPool(
    conninfo=CHECKPOINTER_DATABASE_URL,
    max_size=20,
    kwargs={"autocommit": True, "prepare_threshold": 0},
)

checkpointer = PostgresSaver(connection_pool)


def setup_checkpointer():
    """Idempotent: creates the LangGraph checkpoint tables if they don't exist."""
    checkpointer.setup()
