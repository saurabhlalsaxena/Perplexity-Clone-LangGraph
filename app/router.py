#router.py
from packages.search_utils import perplexity_clone_graph
from fastapi import APIRouter, UploadFile, File, Body, BackgroundTasks
from langserve import add_routes
from langchain_core.messages import BaseMessage, HumanMessage
from langserve.pydantic_v1 import BaseModel
from typing import List, Union, Dict, Any, AsyncIterator
from langchain_core.runnables import chain
from langchain_core.runnables import RunnableLambda

router = APIRouter()

@router.get("/")
async def read_root():
    return {"message": "OK"}

class Input(BaseModel):
    query: str
    thread_id: str

@chain
def custom_chain(input: Input):
    query = input['query']
    thread_id = input['thread_id']

    config = {"configurable": {"thread_id": f'{thread_id}'},"recursion_limit": 20}

    inputs = {
    "messages": [HumanMessage(content=query)],
    }

    output=perplexity_clone_graph.invoke(inputs, config)
    print(output)

    return output

class Output(BaseModel):
    output: Any

add_routes(
    router,
    custom_chain.with_types(input_type=Input, output_type=Output),
    path="/search"
)


