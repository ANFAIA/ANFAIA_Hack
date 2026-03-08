import os
import requests
import urllib.parse
from google import genai
from google.genai import types
from dotenv import load_dotenv
import database

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

IMAGE_DIR = "../frontend/public/image_examples"
OUTPUT_DIR = "../frontend/public/dreams"

os.makedirs(OUTPUT_DIR, exist_ok=True)

mock_coords = [
    (37.7749, -122.4194),
    (34.0522, -118.2437),
    (40.7128, -74.0060),
    (41.8781, -87.6298),
    (51.5074, -0.1278)
]

images = [f for f in os.listdir(IMAGE_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
images.sort()

# Clear database tables to avoid duplicates for now
database.init_db()
conn = database.get_connection()
c = conn.cursor()
c.execute("DELETE FROM discovery_metadata")
c.execute("DELETE FROM memories")
conn.commit()
conn.close()

print(f"Found {len(images)} images in {IMAGE_DIR}")

for idx, img_name in enumerate(images):
    img_path = os.path.join(IMAGE_DIR, img_name)
    print(f"\nProcessing {img_name}...")
    
    with open(img_path, "rb") as f:
        image_bytes = f.read()

    # Get Gemini Description
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                "Describe the main subject of this physical environment or object in one short, clear sentence.",
                types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
            ]
        )
        description = response.text.strip()
    except Exception as e:
        print("Gemini description error:", e)
        description = "A mysterious dream encountered by the bot."
        
    print(f"Vision Analysis: {description}")
    
    # NanoBanana2 (Imagen 3) Mock
    print(f"Synthesizing NanoBanana2 Dream via Imagen 3...")
    out_name = f"dream_{idx}.jpg"
    out_path = os.path.join(OUTPUT_DIR, out_name)

    try:
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
        print(f"Saved dream to {out_path}")
    except Exception as e:
        print("Gemini image generation error:", e)
        # Fallback to pollinations if Gemini fails
        prompt = f"abstract watercolor painting style, {description}"
        pollinations_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=400&height=300&nologo=true"
        r = requests.get(pollinations_url)
        with open(out_path, "wb") as f:
            f.write(r.content)
        print(f"Saved fallback dream to {out_path}")
    
    public_url = f"/dreams/{out_name}"
    original_url = f"/image_examples/{img_name}"
    
    lat = mock_coords[idx % len(mock_coords)][0]
    lng = mock_coords[idx % len(mock_coords)][1]
    
    database.add_discovery(
        description=description,
        type="Environment",
        lat=lat,
        lng=lng,
        embedding=[0.5] * 768,
        image_url=public_url,
        original_image_url=original_url
    )
    
print("\nAll initial dreams have been generated and saved to the shared folder successfully!")
