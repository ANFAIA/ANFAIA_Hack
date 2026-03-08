from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
import database

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
            embedding=discovery.embedding
        )
        return {"status": "ok", "id": discovery_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # Here we will manage the bidi-streaming to Gemini 3.x Live API
    # and handle audio/video chunks from the mobile app.
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
    except Exception as e:
        print(f"WebSocket Error: {e}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
