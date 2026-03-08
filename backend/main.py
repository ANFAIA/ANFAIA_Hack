import asyncio
import json
import ssl
import certifi
import websockets
import google.auth
from google.auth.transport.requests import Request
from fastapi import FastAPI, WebSocket, HTTPException, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
import database
from typing import Optional

app = FastAPI(title="OmniBot Nervous System")

# Setup CORS for the Svelte App
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Discovery(BaseModel):
    description: str
    type: str
    embedding: list[float]
    lat: float = 0.0
    lng: float = 0.0
    image_data: Optional[str] = None


@app.get("/")
async def root():
    return {"status": "ok", "message": "OmniBot Proxy is running"}

@app.get("/discoveries")
async def get_discoveries():
    try:
        data = database.get_all_discoveries()
        return {"data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/discoveries")
async def add_discovery(discovery: Discovery):
    # Enforce basic embedding length rule for the hackathon (Gemini output dummy length 768)
    if len(discovery.embedding) != 768:
        raise HTTPException(status_code=400, detail="Embedding must be 768 dimensions")
    
    try:
        discovery_id = database.add_discovery(
            description=discovery.description,
            type=discovery.type,
            embedding=discovery.embedding,
            lat=discovery.lat,
            lng=discovery.lng
        )
        # Note: image_data is accepted but database schema for discoveries doesn't currently store images.
        # It's prepared here for the prompt request "storage and procesed".
        return {"status": "ok", "id": discovery_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def generate_access_token():
    try:
        creds, _ = google.auth.default()
        if not creds.valid:
            creds.refresh(Request())
        return creds.token
    except Exception as e:
        print(f"Error generating token: {e}")
        return None

async def proxy_to_client(server_ws, client_ws: WebSocket):
    try:
        async for message in server_ws:
            await client_ws.send_text(message)
    except Exception as e:
        print(f"Server to client proxy error: {e}")

async def client_to_proxy(client_ws: WebSocket, server_ws):
    try:
        while True:
            message = await client_ws.receive_text()
            await server_ws.send(message)
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"Client to server proxy error: {e}")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("🔌 New WebSocket client connection...")
    
    try:
        # Wait for the first message from the client (setup payload)
        setup_message = await websocket.receive_text()
        setup_data = json.loads(setup_message)
        
        bearer_token = setup_data.get("bearer_token")
        service_url = setup_data.get("service_url")
        
        # If no bearer token provided, generate one using default credentials
        if not bearer_token:
            print("🔑 Generating access token using default credentials...")
            bearer_token = generate_access_token()
            if not bearer_token:
                await websocket.close(code=1008, reason="Authentication failed")
                return
                
        if not service_url:
            await websocket.close(code=1008, reason="Service URL is required")
            return
            
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {bearer_token}",
        }
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        
        print(f"Connecting to Gemini API: {service_url}")
        async with websockets.connect(
            service_url, additional_headers=headers, ssl=ssl_context
        ) as server_websocket:
            print("✅ Connected to Gemini API")
            
            # Create bidirectional proxy tasks
            client_to_server_task = asyncio.create_task(client_to_proxy(websocket, server_websocket))
            server_to_client_task = asyncio.create_task(proxy_to_client(server_websocket, websocket))
            
            # Wait for either task to complete
            done, pending = await asyncio.wait(
                [client_to_server_task, server_to_client_task],
                return_when=asyncio.FIRST_COMPLETED,
            )
            
            # Cancel the remaining task
            for task in pending:
                task.cancel()
                
    except websockets.exceptions.ConnectionClosed as e:
        print(f"Server connection closed: {e.code} - {e.reason}")
        if not websocket.client_state.name == "DISCONNECTED":
            await websocket.close(code=e.code, reason=e.reason)
    except Exception as e:
        print(f"WebSocket Error: {e}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
