#router.py
from packages.search_utils import perplexity_clone_graph
from fastapi import APIRouter, UploadFile, File, Body, BackgroundTasks
from langserve import add_routes
from langchain_core.messages import BaseMessage, HumanMessage
from langserve.pydantic_v1 import BaseModel
from typing import List, Union, Dict, Any, AsyncIterator
from langchain_core.runnables import chain
from langchain_core.runnables import RunnableLambda
from .db_setup import checkpointer

router = APIRouter()

@router.get("/")
async def read_root():
    return {"message": "OK"}

class Input(BaseModel):
    query: str
    thread_id: str

@router.get("/getresponse")
async def get_reponse(thread_id: Any = Body(...)):
    config = {"configurable": {"thread_id": thread_id}}
    checkpoint =  checkpointer.get(config)
    answer = checkpoint['channel_values']['messages'][1].content
    return {'answer':answer}


@chain
def custom_chain(input: Input):
    query = input['query']
    thread_id = input['thread_id']

    config = {"configurable": {"thread_id": f'{thread_id}'},"recursion_limit": 20}

    inputs = {
    "messages": [HumanMessage(content=query)],
    }

    output=perplexity_clone_graph.invoke(inputs, config)
    answer = output['messages'][-1].content

    return {'answer':answer}

class Output(BaseModel):
    output: Any

add_routes(
    router,
    custom_chain.with_types(input_type=Input),
    path="/search"
)


