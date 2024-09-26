#server.py
import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from langserve import add_routes
from .router import router
#from psycopg.rows import dict_row
#from psycopg_pool import ConnectionPool
#from langgraph.checkpoint.postgres import PostgresSaver

from packages.search_utils import create_graph


from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from langgraph.checkpoint.postgres import PostgresSaver
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres import AsyncPostgresSaver
from .db_setup import DB_URI, connection_kwargs


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[dict[str, Any]]:
    async with AsyncConnectionPool(
        conninfo=DB_URI,
        max_size=20,
        kwargs=connection_kwargs
    ) as pool, pool.connection() as conn:
        checkpointer = AsyncPostgresSaver(conn)
        graph = create_graph(checkpointer)
        yield {"graph": graph}

app = FastAPI(
    title="Perplexity Clone",
    description="First version of perplexity clone",
    version="0.0.1",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def redirect_root_to_docs():
    return RedirectResponse("/docs")

# Edit this to add the chain you want to add
#add_routes(app, NotImplemented)
app.include_router(
    router,
    prefix="/api/v1",
    #dependencies=[Depends(get_user)],
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
