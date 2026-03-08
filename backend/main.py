from fastapi import FastAPI, WebSocket, HTTPException, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
import asyncio
from google import genai
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
    lat: float = 0.0
    lng: float = 0.0


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
        return {"status": "ok", "id": discovery_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dreams/recap")
async def get_dream_recap():
    """
    Collects the discoveries from the last 10 minutes to prepare
    images for the Veo 3.1 video summary.
    """
    try:
        # In a real app, we filter by timestamp > NOW() - 10 minutes
        # For the hackathon, we'll grab the top 10 recent memories
        discoveries = database.get_all_discoveries()[:10]
        
        # Prepare the image prompts and metadata for video creation
        recap_images = []
        for d in discoveries:
            prompt = f"watercolor painting style {d['description']}"
            recap_images.append({
                "id": d["id"],
                "prompt": prompt,
                "lat": d["lat"],
                "lng": d["lng"]
            })
            
        return {
            "status": "ok", 
            "images_prepared": recap_images,
            "message": "Images collected for the 10-minute Dream Video Recap."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # Gemini 2.x Multimodal Live API Setup
    client = genai.Client() # Expects GEMINI_API_KEY environment variable
    model = "gemini-2.0-flash-exp"
    
    try:
        async with client.aio.live.connect(model=model, config={"response_modalities": ["AUDIO"]}) as session:
            print("Connected to Gemini 2.x Live API")
            
            async def receive_from_app():
                try:
                    while True:
                        # Receive video/audio chunks from Svelte App
                        data = await websocket.receive_bytes()
                        # Send to Gemini
                        await session.send(input={"data": data, "mime_type": "audio/pcm"}, end_of_turn=True)
                except WebSocketDisconnect:
                    print("App disconnected")

            async def send_to_app():
                async for response in session.receive():
                    server_content = response.server_content
                    if server_content is not None:
                        model_turn = server_content.model_turn
                        if model_turn is not None:
                            for part in model_turn.parts:
                                if part.inline_data:
                                    # Forward Gemini's audio back to the Svelte App
                                    await websocket.send_bytes(part.inline_data.data)

            await asyncio.gather(receive_from_app(), send_to_app())
            
    except Exception as e:
        print(f"Gemini Live Proxy Error: {e}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
