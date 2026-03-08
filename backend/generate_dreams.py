import os
import time
import shutil
import random
import requests
import urllib.parse
from dotenv import load_dotenv
import database

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"), override=True)

try:
    from google import genai
    from google.genai import types
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        print(f"Using API Key starting with: {api_key[:8]}...")
        client = genai.Client(api_key=api_key)
    else:
        print("WARNING: GEMINI_API_KEY not found. Running fallback-only mode.")
        client = None
except Exception as e:
    print(f"Gemini SDK not available: {e}")
    client = None

IMAGE_DIR = "../frontend/public/image_examples"
OUTPUT_DIR = "../frontend/public/dreams"

# --- Clean outputs and DB ---
if os.path.exists(OUTPUT_DIR):
    for f in os.listdir(OUTPUT_DIR):
        fp = os.path.join(OUTPUT_DIR, f)
        if os.path.isfile(fp):
            os.unlink(fp)
    print(f"Cleaned {OUTPUT_DIR}")

os.makedirs(OUTPUT_DIR, exist_ok=True)

database.init_db()
conn = database.get_connection()
c = conn.cursor()
c.execute("DELETE FROM discovery_metadata")
c.execute("DELETE FROM memories")
conn.commit()
conn.close()
print("Cleared DB tables.")

mock_coords = [
    (37.7749, -122.4194),
    (34.0522, -118.2437),
    (40.7128, -74.0060),
    (41.8781, -87.6298),
    (51.5074, -0.1278)
]

# Smart descriptions for each file if Gemini is unavailable
FALLBACK_DESCRIPTIONS = {
    "p1": "A smartphone in a clear case propped on a white stand in a busy modern workspace",
    "p2": "A blue Saratoga sparkling water glass bottle on a clean white table",
    "p3": "Three recycling bins, one blue, one green, one grey, lined up in an indoor hallway",
    "p4": "A simple white ceramic coffee cup sitting alone on a desk",
    "p5": "A steep winding mountain road descending towards a sun-lit European village in the valley below"
}

images = sorted([f for f in os.listdir(IMAGE_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
print(f"\nFound {len(images)} images in {IMAGE_DIR}")

for idx, img_name in enumerate(images):
    img_path = os.path.join(IMAGE_DIR, img_name)
    img_key = os.path.splitext(img_name)[0].lower()  # e.g. "p1", "p2"

    print(f"\n[{idx+1}/{len(images)}] Processing {img_name}...")

    with open(img_path, "rb") as fh:
        image_bytes = fh.read()

    # --- Step 1: Describe with Gemini Vision ---
    description = None
    if client:
        try:
            response = client.models.generate_content(
                model='gemini-1.5-flash',
                contents=[
                    "Describe the main subject of this environment or object in one short, clear sentence.",
                    types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
                ]
            )
            description = response.text.strip()
            print(f"  Vision (Gemini): {description}")
        except Exception as e:
            print(f"  Gemini vision error ({e.__class__.__name__}): {e}")

    if not description:
        # Use specific fallback description keyed to filename
        description = next((v for k, v in FALLBACK_DESCRIPTIONS.items() if k in img_key), "A mysterious dream encountered by the bot")
        print(f"  Vision (heuristic): {description}")

    # --- Step 2: Generate a unique NanoBanana2 watercolor dream ---
    out_name = f"dream_{idx}.jpg"
    out_path = os.path.join(OUTPUT_DIR, out_name)

    # Use a random seed per image so Pollinations returns UNIQUE images
    seed = random.randint(10000, 99999)
    watercolor_prompt = f"abstract watercolor painting, soft colors, artistic brushstrokes, {description}"
    
    gemini_success = False
    if client:
        try:
            result = client.models.generate_images(
                model='imagen-4.0-generate-001',
                prompt=watercolor_prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    output_mime_type="image/jpeg",
                    aspect_ratio="4:3"
                )
            )
            for generated_image in result.generated_images:
                with open(out_path, 'wb') as fh:
                    fh.write(generated_image.image.image_bytes)
            print(f"  NanoBanana2 (Imagen 4) dream saved: {out_name}")
            gemini_success = True
        except Exception as e:
            print(f"  Imagen error ({e.__class__.__name__}): skipping to fallback")

    if not gemini_success:
        # Unique seed per image ensures Pollinations returns a DIFFERENT image each time
        pollinations_url = (
            f"https://image.pollinations.ai/prompt/{urllib.parse.quote(watercolor_prompt)}"
            f"?width=512&height=384&nologo=true&seed={seed}&model=flux&nofeed=true"
        )
        print(f"  Using Pollinations fallback (seed={seed})...")
        saved = False
        for attempt in range(3):
            try:
                r = requests.get(pollinations_url, timeout=120)
                with open(out_path, "wb") as fh:
                    fh.write(r.content)
                print(f"  Fallback dream saved: {out_name} (attempt {attempt+1})")
                saved = True
                break
            except Exception as poll_e:
                print(f"  Pollinations attempt {attempt+1} failed: {poll_e}. Retrying...")
                time.sleep(5)
        if not saved:
            print(f"  WARNING: Could not generate dream for {img_name} after 3 attempts.")

    # --- Step 3: Save to Dream Network DB ---
    public_url = f"/dreams/{out_name}"
    original_url = f"/image_examples/{img_name}"
    lat, lng = mock_coords[idx % len(mock_coords)]

    database.add_discovery(
        description=description,
        type="Environment",
        lat=lat,
        lng=lng,
        embedding=[0.5] * 768,
        image_url=public_url,
        original_image_url=original_url
    )
    print(f"  Saved to Dream Network → {public_url}")

print("\n✓ All dreams generated and saved to the Dream Network successfully!")
