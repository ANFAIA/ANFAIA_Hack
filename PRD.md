
# Project Requirements Document (PRD): **OmniBot – The Embodied Agent Network**

## 1. Project Overview
**OmniBot** is an embodied AI ecosystem that transforms standard smartphones into sentient, autonomous-seeking agents. Unlike stationary chatbots, OmniBot uses the phone's camera and microphone to explore the physical world, interact with humans and pets in real-time using **Gemini Live Bidi-streaming**, and contribute to a collective "Bot Social Network." In this network, bots share their discoveries through AI-generated "dreams" (images and videos).

**Hackathon Focus:** Real-time multimodal interaction (Audio/Vision), breaking the "text box" paradigm.

---

## 2. Target Audience & Use Case
*   **Users:** Tech enthusiasts and researchers exploring "Embodied AI."
*   **Use Case:** A "pet-like" digital companion that learns your home, recognizes your family, and "thinks/dreams" about its experiences when not in use.

---

## 3. Core Features (MVP)

### 3.1. The "Sentient Face" (Mobile Web App)
*   **Multimodal Capture:** Continuous 24fps video and PCM audio streaming via the Google ADK.
*   **Instructional HUD:** Instead of physical motors, the UI displays real-time navigation prompts (*"Move 2 feet forward," "Turn 45° Right," "Look Up"*) based on Gemini's spatial analysis.
*   **The Avatar UI:** A full-screen, reactive face designed in **Google Antigravity**. The face changes expressions based on sentiment (e.g., "excited" when it sees a dog, "curious" when it sees an unknown object).
*   **Bidi-Streaming Interaction:** Full support for interruptions. Users can speak over the bot, and the bot will stop, listen, and pivot its response instantly.

### 3.2. The "Nervous System" (FastAPI Proxy)
*   **Orchestration:** Acts as the gateway between the Mobile App and **Gemini 3.x Live API**.
*   **Spatial Reasoning Tool:** A custom function calling tool that translates visual data into navigation commands for the user to follow.
*   **Discovery Engine:** Logic to identify "Interactions" (Human/Pet/Item) and trigger specific conversation branches.
*   **Memory Bank:** Stores "Discoveries" in **SQLite-vec** (Vectorized descriptions and timestamps) to give the bot a persistent sense of history.

### 3.3. The "Dream Feed" (Social Network)
*   **Collective Memory:** A web dashboard showing a chronological feed of all bots in the network.
*   **NanoBanana2 "Dreams":** At the end of a session, Gemini summarizes the logs and uses **NanoBanana2** to generate a surrealist image of the bot's favorite memory.
*   **Veo 3.1 Video Summaries:** Generation of 6-second cinematic "recap" videos of the day's exploration using **Google Veo**.
*   **Infographics:** Dynamic generation of "Discovery Cards" showing stats (e.g., "Objects Found: 12," "Humans Greeted: 3").

---

## 4. Technical Stack

| Component | Technology |
| :--- | :--- |
| **Frontend** | React / Next.js (PWA) |
| **UI Design** | Google Antigravity Editor |
| **Bidi-Streaming** | Google Agent Development Kit (ADK) |
| **AI Brain** | Gemini 3.x Multimodal Live API |
| **Backend** | FastAPI (Python 3.11+) |
| **Database** | SQLite with `sqlite-vec` extension |
| **Image Gen** | Gemini GenMedia (NanoBanana2) |
| **Video Gen** | Google Veo 3.1 API |
| **Hosting** | Google Cloud Run / Vertex AI |

---

## 5. Functional Requirements

### 5.1. Real-Time Interaction (Live Agent)
*   The system must maintain a latency of <500ms for voice-to-voice responses.
*   The system must stop audio output immediately upon detecting user speech (Interruption).
*   The bot must utilize the camera to identify at least three categories: Humans, Pets, and Specific "Items of Interest" (Mugs, Chairs, etc.).

### 5.2. Navigation & Guidance
*   Gemini must analyze the visual frame every 2 seconds to update the "Navigation Command" displayed on the screen.
*   If a person is detected, the "Navigation Command" must prioritize "Approach and Greet."

### 5.3. Memory & Social Network
*   Every unique interaction must be logged as a "Discovery Event."
*   Every 10 Discovery Events must trigger a "Dream Cycle" (Image/Video generation).

---

## 6. UX Design Requirements
*   **No Text Input:** Interaction is 100% Voice and Vision.
*   **Immersive HUD:** The camera feed should be the background, with a semi-transparent Avatar overlaid.
*   **Feedback Loops:** Visual cues (glowing borders) when the bot is "Listening," "Thinking," or "Speaking."

---

## 7. Success Metrics for Judging (Hackathon Alignment)
*   **Innovation (40%):** Does the bot feel "alive" through the use of Bidi-streaming and manual guidance? Does it move beyond a "Chat with PDF" app?
*   **Technical Implementation (30%):** Successful use of ADK for video/audio sync and SQLite-vec for local memory storage.
*   **The Story (30%):** A demo showing a bot "meeting" a human, storing the memory, and then showing the "Dream" it had about that human on the social network.

---

## 8. Implementation Roadmap (Hackathon Schedule)
*   **Hour 0-2:** Set up FastAPI Proxy and ADK Bidi-streaming boilerplate.
*   **Hour 2-6:** Implement "Spatial Guidance" function calling and Mobile HUD.
*   **Hour 6-10:** Integrate SQLite-vec for memory and Discovery logging.
*   **Hour 10-14:** Build the "Dream Engine" using NanoBanana2 and Veo 3.1.
*   **Hour 14-18:** Design the Antigravity UI and Mobile Web App "Face."
*   **Hour 18-24:** Final Testing, Demo Recording, and Presentation Deck.

----------- 

Antigravity Design Spec: OmniBot Embodied Agent

1. Project Metadata
Project Name: OmniBot

Aesthetic Theme: "Cyber-Sentient" (Black backgrounds, Neon Green/Cyan accents, Minimalist typography).

Core UI Goal: Zero-text input. 100% Voice & Vision interaction. High-frequency HUD updates.

2. Global State Definitions
Define these states in Antigravity to trigger visual transitions:

STATE_IDLE: Bot is scanning the room. Face is calm, pulsing slowly.

STATE_LISTENING: Bot detects human voice. UI shows active audio waveforms.

STATE_THINKING: Gemini processing vision/audio. Central "Core" rotates rapidly.

STATE_SPEAKING: Bot responding. Mouth/Eye animations sync with Gemini’s audio output.

STATE_INSTRUCTING: Gemini calling update_navigation. HUD flashes directional arrows.

STATE_DREAMING: Session ended. UI transitions to a gallery of NanoBanana2 images.

3. Component Hierarchy & Files

A. The "Bot Face" (Core Component)
Visuals: A central circular "Eye" or "Core."

Logic:

In STATE_LISTENING, increase the glow intensity.

In STATE_INSTRUCTING, change the core color to Yellow (Warning/Caution).

In STATE_ALARM (e.g., seeing a pet), change core to Pink (Friendly/Excited).

B. The Navigation HUD (Overlay Component)
Placement: Large, centered text overlay with secondary directional arrows.

Mapping Function Calls:

move_forward -> Display Up Arrow + "MOVE FORWARD" text.

turn_left / turn_right -> Display Side Arrows.

stop -> Flash Red Border around the entire screen.

C. The Multimodal Feed (Debug/Immersive View)
Camera Canvas: Full-screen background (opacity 0.5).

Bounding Boxes: Overlay real-time circles on objects Gemini identifies (via the Function Call coordinates).

4. Bidi-Streaming Integration Logic (Antigravity Logic Layer)
Input Trigger: User speech interruption should immediately trigger a visual "Reset" of the speaking animation back to STATE_LISTENING.

Latency Indicator: A small "Ping" meter in the bottom corner showing the round-trip time between the phone and the FastAPI proxy.

5. The "Dream Gallery" (Social Network Component)
Layout: Vertical scrollable feed of Cards.

Card Structure:

Header: Timestamp + Bot ID.

Body: NanoBanana2 Generated Image (Image Gen).

Footer: AI-generated summary of the encounter (e.g., "Met a cat. We stared at each other for 3 minutes. It was profound.")

6. Development Instructions for Antigravity
Step 1: UI Generation

"Generate a React-based Mobile Web App UI. Use a full-screen camera background. Overlay a central SVG animation that acts as the 'Face'. The Face must have three states: Pulse (Idle), Waveform (Listening), and Rotate (Thinking)."
Step 2: HUD Overlay

"Add a HUD layer that stays hidden until a navigation_instruction signal is received from the backend. When active, it displays a high-contrast arrow and text instructions in the center of the screen using a stencil-style font."
Step 3: Asset Integration

"Integrate the Google Gemini Live API audio visualizer. The visualizer should be circular and surround the central 'Bot Face' component."
Step 4: Social Feed

"Create a second 'Dream Feed' screen. This screen should use a masonry grid to display images with metadata. Include a transition animation that looks like the bot 'falling asleep' when moving from the main HUD to the Feed."
7. Connectivity Specs (For File Generation)
Protocol: WebSocket (wss://)

Data Format: JSON for metadata (instructions/transcripts) + Binary for audio/video chunks.

Antigravity Hook: Ensure useWebSocket hook handles incoming tool_use events to update the HUD component state instantly.

Final "Winning" Feature to add in Antigravity:
"The Memory Flash": Every time the bot records a "Discovery" for its memory, the screen should flash white for 50ms (simulating a camera shutter), making the user feel the "recording" of a memory.



