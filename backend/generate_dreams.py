import os
import requests
import urllib.parse
import database


IMAGE_DIR = "../docs/image_examples"
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
conn = database.get_connection()
c = conn.cursor()
c.execute("DELETE FROM discovery_metadata")
c.execute("DELETE FROM memories")
conn.commit()
conn.close()

print(f"Found {len(images)} images in {IMAGE_DIR}")

mock_descriptions = {
    "p1.JPG": "An empty wooden chair in a room.",
    "p2.jpg": "A small white dog sitting down.",
    "p3.JPG": "A sleek motorcycle parked outdoors.",
    "p4.jpg": "A fluffy white cat resting indoors.",
    "p5.JPG": "A steep paved road leading downwards."
}

for idx, img_name in enumerate(images):
    img_path = os.path.join(IMAGE_DIR, img_name)
    print(f"\nProcessing {img_name}...")
    
    description = mock_descriptions.get(img_name, "A mysterious dream encountered by the bot.")
        
    print(f"Vision Analysis: {description}")
    
    # NanoBanana2 Mock via pollinations
    prompt = f"abstract watercolor painting style, {description}"
    pollinations_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=400&height=300&nologo=true"
    
    print(f"Synthesizing NanoBanana2 Dream from Gemini text...")
    r = requests.get(pollinations_url)
    
    out_name = f"dream_{idx}.jpg"
    out_path = os.path.join(OUTPUT_DIR, out_name)
    with open(out_path, "wb") as f:
        f.write(r.content)
        
    print(f"Saved dream to {out_path}")
    
    public_url = f"/dreams/{out_name}"
    
    lat = mock_coords[idx % len(mock_coords)][0]
    lng = mock_coords[idx % len(mock_coords)][1]
    
    database.add_discovery(
        description=description,
        type="Environment",
        lat=lat,
        lng=lng,
        embedding=[0.5] * 768,
        image_url=public_url
    )
    
print("\nAll initial dreams have been generated and saved to the shared folder successfully!")
