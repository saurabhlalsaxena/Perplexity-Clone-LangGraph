#router.py
from packages.search_utils import create_graph #perplexity_clone_graph
from fastapi import APIRouter, UploadFile, File, Body, BackgroundTasks, WebSocket, WebSocketDisconnect, Request, Depends
from langserve import add_routes
from langchain_core.messages import BaseMessage, HumanMessage
from langserve.pydantic_v1 import BaseModel
from typing import List, Union, Dict, Any, AsyncIterator
from langchain_core.runnables import chain
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables import RunnableParallel, RunnableLambda
from .db_setup import checkpointer, DB_URI, connection_kwargs
import json
import asyncio
import traceback
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
        else:
            print("Attempted to disconnect a WebSocket that was not in the active connections list")

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

@chain
async def custom_chain(input: Input):
    query = input['query']
    thread_id = input['thread_id']

    config = {"configurable": {"thread_id": f'{thread_id}'},"recursion_limit": 20}

    inputs = {
    "messages": [HumanMessage(content=query)],
    }

    #output=perplexity_clone_graph.invoke(inputs, config)
    #output = await request.state.graph.ainvoke(inputs, config)
    async with AsyncConnectionPool(
    # Example configuration
    conninfo=DB_URI,
    max_size=20,
    kwargs=connection_kwargs,) as pool:
        checkpointer = AsyncPostgresSaver(pool)

        # NOTE: you need to call .setup() the first time you're using your checkpointer
        #await checkpointer.setup()

        graph = create_graph(checkpointer=checkpointer)
        output = await graph.ainvoke(
            inputs, config
        )

    #checkpoint = await checkpointer.aget(config)

    answer = output['messages'][-1].content

    return {'answer':answer}

class Output(BaseModel):
    output: Any

add_routes(
    router,
    custom_chain.with_types(input_type=Input),
    path="/search"
)

@router.post("/getresponse")
async def get_reponse(thread_id: Any = Body(...)):
    thread_id = thread_id['thread_id']
    config = {"configurable": {"thread_id": f'{thread_id}'}}
    checkpoint =  checkpointer.get(config)
    answer = checkpoint['channel_values']['messages'][1].content
    return {'answer':checkpoint}

@router.post("/getcheckpoint")
async def get_checkpoint(thread_id: Any = Body(...)):
    thread_id = thread_id['thread_id']
    config = {"configurable": {"thread_id": f'{thread_id}'}}
    checkpoint =  checkpointer.get(config)
    return {'checkpoint':checkpoint}

@router.post("/listcheckpoints")
async def list_checkpoints(thread_id: Any = Body(...)):
    thread_id = thread_id['thread_id']
    config = {"configurable": {"thread_id": f'{thread_id}'}}
    checkpoint_list =  checkpointer.list(config)
    return {'checkpoint_list':checkpoint_list}

# @router.websocket("/ws/search")
# async def websocket_custom_chain(websocket: WebSocket):
#     await manager.connect(websocket)
#     try:
#         while True:
#             try:
#                 data = await asyncio.wait_for(websocket.receive_text(), timeout=5.0)
#                 print(f"Received data: {data}")
#                 parsed_data = json.loads(data)
                
#                 input_data = Input(**parsed_data)
                
#                 config = {
#                     "configurable": {"thread_id": input_data.thread_id},
#                     "recursion_limit": 20
#                 }
                
#                 inputs = {
#                     "messages": [HumanMessage(content=input_data.query)],
#                 }
                
#                 try:
#                     print("Starting perplexity_clone_graph.invoke")
#                     #output = await asyncio.to_thread(perplexity_clone_graph.invoke, inputs, config)
#                     print(f"perplexity_clone_graph.invoke completed. Output: {output}")
                    
#                     if output is None or 'messages' not in output or len(output['messages']) == 0:
#                         raise ValueError("Invalid output from perplexity_clone_graph.invoke")
                    
#                     answer = output['messages'][-1].content
#                     print(f"Answer: {answer}")
                    
#                     response_json = json.dumps({"answer": answer})
#                     print(f"Sending response: {response_json}")
#                     await websocket.send_text(response_json)
#                     print("Response sent successfully")
                
#                 except asyncio.TimeoutError:
#                     print("Operation timed out")
#                     await websocket.send_text(json.dumps({"error": "The operation timed out"}))
                
#                 except Exception as e:
#                     print(f"Error processing query: {str(e)}")
#                     print(traceback.format_exc())
#                     await websocket.send_text(json.dumps({"error": f"An error occurred: {str(e)}"}))
            
#             except asyncio.TimeoutError:
#                 print("WebSocket receive timed out")
#                 await websocket.send_text(json.dumps({"error": "WebSocket receive timed out"}))
            
#             except WebSocketDisconnect:
#                 print("WebSocket disconnected")
#                 break
    
#     except Exception as e:
#         print(f"An error occurred: {str(e)}")
#         print(traceback.format_exc())
#     finally:
#         print("Closing WebSocket connection")
#         await manager.disconnect(websocket)
