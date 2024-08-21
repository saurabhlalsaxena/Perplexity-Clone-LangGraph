# app/db_setup.py
import os
from dotenv import load_dotenv
from psycopg import Connection
from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row
from langgraph.checkpoint.postgres import PostgresSaver

# Load environment variables
load_dotenv()

DB_URI = os.getenv('DATABASE_URL')

connection_kwargs ={
    "autocommit": True,
    "prepare_threshold": 0,
    "row_factory": dict_row,
}

pool = ConnectionPool(
    conninfo=DB_URI,
    max_size=20,
    kwargs=connection_kwargs
)

conn = pool.getconn()

checkpointer = PostgresSaver(conn)