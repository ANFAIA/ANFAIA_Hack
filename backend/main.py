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

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"), override=True)
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
                model='nano-banana-pro-preview',
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

@app.get("/bot/instruct")
async def bot_instruct():
    """
    Called by the bot when it sees nothing interesting.
    Returns a short exploration instruction from the Gemini brain.
    """
    if not client:
        return {"instruction": "EXPLORE FORWARD"}
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=(
                "You are the brain of OmniBot, a curious robot exploring the world. "
                "Its camera sees nothing interesting right now. "
                "Reply with ONE short movement instruction, max 4 words, ALL CAPS. "
                "Examples: TURN LEFT, MOVE FORWARD, SCAN AREA, LOOK UP, ROTATE SLOWLY."
            )
        )
        return {"instruction": response.text.strip().upper()[:40]}
    except Exception as e:
        print("Brain instruct error:", e)
        return {"instruction": "SCANNING..."}

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
    print("Frontend connected to /ws proxy")

    # Live API model for bidiGenerateContent (native audio, v1beta)
    LIVE_MODEL = "gemini-2.5-flash-native-audio-preview-12-2025"
    LIVE_CONFIG = {
        "response_modalities": ["AUDIO"],
        "system_instruction": (
            "You are OmniBot, a curious, friendly, sentient robot exploring the world. "
            "Speak with warmth and wonder. You notice things around you and dream about them. "
            "Keep responses short and conversational."
        ),
    }

    if not client:
        await websocket.send_json({"error": "GEMINI_API_KEY not configured on server."})
        await websocket.close()
        return

    try:
        async with client.aio.live.connect(model=LIVE_MODEL, config=LIVE_CONFIG) as session:
            print(f"Connected to Gemini Live API ({LIVE_MODEL})")

            import base64

            # Trigger the bot to greet the user immediately on connection
            await session.send_client_content(
                turns=[{"role": "user", "parts": [{"text": "Hello! Please introduce yourself in one short sentence."}]}],
                turn_complete=True
            )

            async def receive_from_app():
                """Forward raw PCM audio bytes from browser → Gemini Live."""
                try:
                    while True:
                        data = await websocket.receive_bytes()
                        await session.send_realtime_input(
                            audio={
                                "data": base64.b64encode(data).decode(),
                                "mime_type": "audio/pcm;rate=16000"
                            }
                        )
                except WebSocketDisconnect:
                    print("Frontend disconnected from /ws")

            async def send_to_app():
                """Forward Gemini Live audio responses → browser."""
                async for response in session.receive():
                    sc = response.server_content
                    if sc and sc.model_turn:
                        for part in sc.model_turn.parts:
                            if part.inline_data:
                                raw = part.inline_data.data
                                # SDK may return bytes or base64 string depending on version
                                if isinstance(raw, bytes):
                                    audio_b64 = base64.b64encode(raw).decode()
                                else:
                                    audio_b64 = raw  # already base64 string
                                await websocket.send_json({"type": "audio", "data": audio_b64})
                    if sc and sc.turn_complete:
                        await websocket.send_json({"type": "turn_complete"})

            await asyncio.gather(receive_from_app(), send_to_app())

    except Exception as e:
        print(f"Gemini Live Proxy Error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
