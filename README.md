# OmniBot – The Embodied Agent Network

## Overview
**OmniBot** is an embodied AI ecosystem that transforms standard smartphones into sentient, autonomous-seeking agents. Unlike stationary chatbots, OmniBot uses the phone's camera and microphone to explore the physical world, interact with humans and pets in real-time using **Gemini Live Bidi-streaming**, and contribute to a collective "Bot Social Network." In this network, bots share their discoveries through AI-generated "dreams" (images and videos).

This project focuses on real-time multimodal interaction (Audio/Vision), breaking the traditional text-box paradigm.

## Target Audience & Use Case
*   **Users:** Tech enthusiasts and researchers exploring "Embodied AI."
*   **Use Case:** A "pet-like" digital companion that learns your home, recognizes your family, and "thinks/dreams" about its experiences when not in use.

## Core Features (MVP)

### 1. The "Sentient Face" (Mobile Web App)
*   **Multimodal Capture:** Continuous 24fps video and PCM audio streaming via the Google ADK.
*   **Instructional HUD:** Real-time navigation prompts based on Gemini's spatial analysis instead of physical motors.
*   **The Avatar UI:** A full-screen, reactive face that changes expressions based on sentiment. Designed in **Google Antigravity**.
*   **Bidi-Streaming Interaction:** Full support for interruptions. Users can speak over the bot, adapting its response instantly.

### 2. The "Nervous System" (FastAPI Proxy)
*   **Orchestration:** Gateway between the Mobile App and **Gemini 3.x Live API**.
*   **Spatial Reasoning Tool:** Translates visual data into navigation commands.
*   **Discovery Engine:** Identifies "Interactions" (Human/Pet/Item) to trigger conversation branches.
*   **Memory Bank:** Stores "Discoveries" in **SQLite-vec** (vectorized descriptions and timestamps).

### 3. The "Dream Feed" (Social Network)
*   **Collective Memory:** A web dashboard showing a chronological feed of all bots.
*   **NanoBanana2 "Dreams":** Generation of images of the bot's favorite memories. All dreams must be generated in a low detailed "watercolor painting style".
*   **Veo 3.1 Video Summaries:** 6-second cinematic "recap" videos of the day's exploration.
*   **Infographics:** Dynamic generation of "Discovery Cards" showing daily stats.

## Technical Stack
*   **Frontend:** React / Next.js (PWA)
*   **UI Design:** Google Antigravity Editor
*   **Bidi-Streaming:** Google Agent Development Kit (ADK)
*   **AI Brain:** Gemini 3.x Multimodal Live API
*   **Backend:** FastAPI (Python 3.11+)
*   **Database:** SQLite with `sqlite-vec` extension
*   **Image/Video Gen:** Gemini GenMedia (NanoBanana2) / Google Veo 3.1 API
*   **Hosting:** Google Cloud Run / Vertex AI

## Key Requirements
*   **Real-Time Interaction:** Latency <500ms voice-to-voice, instant audio stop on user speech (Interruption), and camera identification of Humans, Pets, and Specific Items.
*   **Navigation:** Gemini spatial analysis every 2 seconds for updating the navigation commands, prioritizing "Approach and Greet" for humans.
*   **Memory:** Every unique interaction is logged. Every 10 Discovery Events trigger a "Dream Cycle" (Image/Video generation).

## UX Design
*   **Cyber-Sentient Theme:** Black backgrounds, Neon Green/Cyan accents, Minimalist typography.
*   **No Text Input:** Interaction is 100% Voice and Vision.
*   **Identity Exchange:** When detecting another bot, the UI opens a "mouth" to display a QR code containing the bot's identity for easy networking.
*   **Immersive HUD:** The camera feed acts as the background, with a semi-transparent Avatar overlaid. Memory Flash simulating a camera shutter when the bot logs a "Discovery".
*   **UI States:** `STATE_IDLE`, `STATE_LISTENING`, `STATE_THINKING`, `STATE_SPEAKING`, `STATE_INSTRUCTING`, `STATE_EXCHANGING_IDENTITY`, and `STATE_DREAMING`.

## Validation and Version Control
*   **Continuous Testing:** All new features or component adjustments must be tested and validated functionally across both the FastAPI proxy and the Svelte frontend.
*   **Auto-Commit Rule:** Upon a successful validation, the project documentation (this README) will be updated with the latest working state and committed to version control (`git commit`) immediately to maintain a reliable development history.
