import requests

API_URL = "http://127.0.0.1:8000/discoveries"

mock_dreams = [
    {
        "description": "Saw an empty red chair inside a house.",
        "type": "Object",
        "lat": 37.7749,
        "lng": -122.4194,
        "image_url": "/image_examples/p1.JPG",
        "embedding": [0.1] * 768
    },
    {
        "description": "A close up view of a small white dog sitting on a blue carpet.",
        "type": "Pet",
        "lat": 34.0522,
        "lng": -118.2437,
        "image_url": "/image_examples/p2.jpg",
        "embedding": [0.2] * 768
    },
    {
        "description": "Found a cool looking motorcycle parked on a dirt trail.",
        "type": "Vehicle",
        "lat": 40.7128,
        "lng": -74.0060,
        "image_url": "/image_examples/p3.JPG",
        "embedding": [0.3] * 768
    },
    {
        "description": "Discovered a fluffy white cat resting comfortably indoors.",
        "type": "Pet",
        "lat": 41.8781,
        "lng": -87.6298,
        "image_url": "/image_examples/p4.jpg",
        "embedding": [0.4] * 768
    },
    {
        "description": "Looking down a steep paved road ending near mountain structures.",
        "type": "Location",
        "lat": 51.5074,
        "lng": -0.1278,
        "image_url": "/image_examples/p5.JPG",
        "embedding": [0.5] * 768
    }
]

print("Seeding database with images from docs/image_examples...")
for dream in mock_dreams:
    response = requests.post(API_URL, json=dream)
    if response.status_code == 200:
        print(f"✅ Added Dream: {dream['description'][:30]}...")
    else:
        print(f"❌ Error Adding Dream: {response.text}")
print("Seed complete.")
