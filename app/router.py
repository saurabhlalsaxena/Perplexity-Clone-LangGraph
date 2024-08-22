#router.py
from packages.search_utils import perplexity_clone_graph
from fastapi import APIRouter, UploadFile, File, Body, BackgroundTasks, WebSocket, WebSocketDisconnect
from langserve import add_routes
from langchain_core.messages import BaseMessage, HumanMessage
from langserve.pydantic_v1 import BaseModel
from typing import List, Union, Dict, Any, AsyncIterator
from langchain_core.runnables import chain
from langchain_core.runnables import RunnableLambda
from .db_setup import checkpointer
import json
import asyncio

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        #logging.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            #logging.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
        else:
            print("Attempted to disconnect a WebSocket that was not in the active connections list")
            #logging.warning("Attempted to disconnect a WebSocket that was not in the active connections list")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()



@router.get("/")
async def read_root():
    return {"message": "OK"}

class Input(BaseModel):
    query: str
    thread_id: str

@router.post("/getresponse")
async def get_reponse(thread_id: Any = Body(...)):
    thread_id = thread_id['thread_id']
    config = {"configurable": {"thread_id": f'{thread_id}'}}
    checkpoint =  checkpointer.get(config)
    answer = checkpoint['channel_values']['messages'][1].content
    return {'answer':checkpoint}


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


@router.websocket("/ws/search")
async def websocket_custom_chain(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received data: {data}")
            parsed_data = json.loads(data)
            
            try:
                input_data = Input(**parsed_data)
            except ValueError as e:
                await manager.send_personal_message(json.dumps({"error": f"Invalid input: {str(e)}"}), websocket)
                continue
            
            config = {
                "configurable": {"thread_id": input_data.thread_id},
                "recursion_limit": 20
            }
            
            inputs = {
                "messages": [HumanMessage(content=input_data.query)],
            }
            
            try:
                #output = perplexity_clone_graph.invoke(inputs, config)
                # Use asyncio.wait_for to set a timeout for the long-running operation
                output = await asyncio.wait_for(
                    asyncio.to_thread(perplexity_clone_graph.invoke, inputs, config),
                    timeout=150.0  # Set timeout to 70 seconds
                )
                answer = output['messages'][-1].content
                print(answer)
                
                response = Output(answer=answer)
                response_json = json.dumps(response.dict())
                print(f"Sending response: {response_json}")
                #await manager.send_personal_message(json.dumps(response.dict()), websocket)
                await websocket.send_text(response_json)
            except Exception as e:
                print(f"Error processing query: {str(e)}")
                await manager.send_personal_message(json.dumps({"error": "An error occurred while processing your request"}), websocket)
            
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        manager.disconnect(websocket)