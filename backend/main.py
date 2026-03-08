from fastapi import FastAPI, WebSocket
import uvicorn

app = FastAPI(title="OmniBot Nervous System")

@app.get("/")
async def root():
    return {"status": "ok", "message": "OmniBot Proxy is running"}

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
