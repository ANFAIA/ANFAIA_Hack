from fastapi import FastAPI, WebSocket, HTTPException, WebSocketDisconnect, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
import asyncio
import os
import requests
import urllib.parse
from dotenv import load_dotenv
from google import genai
from google.genai import types
import database

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

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
    image_url: str = ""
    original_image_url: str = ""


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
            lng=discovery.lng,
            image_url=discovery.image_url,
            original_image_url=discovery.original_image_url
        )
        return {"status": "ok", "id": discovery_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/bot/discover")
async def bot_discover(file: UploadFile = File(...), lat: float = Form(0.0), lng: float = Form(0.0)):
    """
    Simulates the Bot uploading a frame from its camera. Uses Gemini to analyze 
    the frame and immediately generates a NanoBanana2 Dream via Imagen 3.
    """
    image_bytes = await file.read()
    
    # 1. Analyze with Gemini
    description = "A mysterious dream encountered by the bot."
    if client:
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[
                    "Describe the main subject of this physical environment or object in one short, clear sentence.",
                    types.Part.from_bytes(data=image_bytes, mime_type=file.content_type or "image/jpeg")
                ]
            )
            description = response.text.strip()
        except Exception as e:
            print("Gemini analysis error:", e)
    
    # 1.1 Save the actual incoming file so the bot can view the original image
    uploads_dir = "../frontend/public/uploads"
    os.makedirs(uploads_dir, exist_ok=True)
    count_val = database.get_connection().cursor().execute('SELECT COUNT(*) FROM discovery_metadata').fetchone()[0]
    
    orig_name = f"bot_orig_{count_val}.jpg"
    with open(os.path.join(uploads_dir, orig_name), "wb") as f_orig:
        f_orig.write(image_bytes)
    original_url = f"/uploads/{orig_name}"
    
    # 2. Generate NanoBanana2 Dream
    output_dir = "../frontend/public/dreams"
    os.makedirs(output_dir, exist_ok=True)
    out_name = f"bot_dream_{count_val}.jpg"
    out_path = os.path.join(output_dir, out_name)
    public_url = f"/dreams/{out_name}"
    
    try:
        if client:
            result = client.models.generate_images(
                model='imagen-3.0-generate-001',
                prompt=f"abstract watercolor painting style, {description}",
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    output_mime_type="image/jpeg",
                    aspect_ratio="4:3"
                )
            )
            for generated_image in result.generated_images:
                with open(out_path, 'wb') as f:
                    f.write(generated_image.image.image_bytes)
        else:
            raise Exception("No Gemini client configured.")
    except Exception as e:
        print("Gemini imagen error, falling back to pollinations:", e)
        prompt = f"abstract watercolor painting style, {description}"
        pollinations_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=400&height=300&nologo=true"
        r = requests.get(pollinations_url)
        with open(out_path, "wb") as f:
            f.write(r.content)
            
    # 3. Save to database
    discovery_id = database.add_discovery(
        description=description,
        type="Environment",
        lat=lat,
        lng=lng,
        embedding=[0.5] * 768,
        image_url=public_url,
        original_image_url=original_url
    )
    
    return {"status": "ok", "discovery_id": discovery_id, "image_url": public_url, "original_image_url": original_url, "description": description}

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
                "lng": d["lng"],
                "image_url": d["image_url"] if "image_url" in d.keys() else "",
                "original_image_url": d["original_image_url"] if "original_image_url" in d.keys() else ""
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
