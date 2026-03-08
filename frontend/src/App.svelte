<script lang="ts">
  import { onMount, tick } from "svelte";
  import * as tf from "@tensorflow/tfjs";
  import * as cocoSsd from "@tensorflow-models/coco-ssd";

  // Routing
  const isSocialPage = window.location.pathname === "/social";

  type BotState =
    | "STATE_IDLE"
    | "STATE_LISTENING"
    | "STATE_THINKING"
    | "STATE_SPEAKING"
    | "STATE_INSTRUCTING"
    | "STATE_EXCHANGING_IDENTITY";
  let currentState: BotState = "STATE_IDLE";

  // Bidi-streaming placeholder HUD text
  let instruction = "ALL CLEAR";

  // Bot Identity Mock
  const botId = "OMNIBOT-A1";
  const qrCodeUrl = `https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${botId}`;

  // Simulate state switching for testing
  function setState(state: BotState) {
    currentState = state;
  }

  // Social Network Data (Dreams)
  let discoveries: any[] = [];

  async function fetchDreams() {
    try {
      const resp = await fetch("http://localhost:8000/discoveries");
      if (resp.ok) {
        const payload = await resp.json();
        discoveries = payload.data;
      }
    } catch (err) {
      console.error("Failed to load dreams:", err);
    }
  }

  // Camera & Streaming Logic
  let videoElement: HTMLVideoElement;
  let leftEyeVideo: HTMLVideoElement;
  let rightEyeVideo: HTMLVideoElement;
  let streamMode = "NONE"; // PICTURES, VIDEO_AUDIO, AUDIO_QR
  let activeStream: MediaStream | null = null;

  // Eye Animation State
  let blink = false;
  let eyeOffsetX = 0;
  let eyeOffsetY = 0;

  // Mouth Emotion State
  let emotion = "happy"; // 'happy', 'sad', 'surprise', 'neutral'

  function startEyeBehaviors() {
    // Random Blinking
    setInterval(
      () => {
        blink = true;
        setTimeout(() => (blink = false), 150);

        if (Math.random() > 0.8) {
          setTimeout(() => {
            blink = true;
            setTimeout(() => (blink = false), 150);
          }, 250);
        }
      },
      3000 + Math.random() * 4000,
    );

    // Random Looking Around
    setInterval(
      () => {
        if (
          currentState === "STATE_IDLE" ||
          currentState === "STATE_LISTENING" ||
          currentState === "STATE_THINKING"
        ) {
          const distance = currentState === "STATE_THINKING" ? 30 : 15;
          eyeOffsetX = Math.random() * distance * 2 - distance;
          eyeOffsetY = Math.random() * distance * 2 - distance;
        } else {
          eyeOffsetX = 0;
          eyeOffsetY = 0;
        }
      },
      1500 + Math.random() * 1000,
    );

    // Random Emotions (Gestures)
    setInterval(
      () => {
        if (
          currentState === "STATE_IDLE" ||
          currentState === "STATE_LISTENING"
        ) {
          const r = Math.random();
          if (r > 0.8) emotion = "surprise";
          else if (r > 0.6) emotion = "sad";
          else if (r > 0.3) emotion = "happy";
          else emotion = "neutral";
        } else {
          emotion = "neutral"; // Reset if active
        }
      },
      5000 + Math.random() * 4000,
    );
  }

  let cocoModel: null | cocoSsd.ObjectDetection = null;

  onMount(async () => {
    if (isSocialPage) {
      fetchDreams();
      return;
    }

    startEyeBehaviors();

    try {
      // Load Tensorflow Model First
      instruction = "INITIALIZING AI...";
      cocoModel = await cocoSsd.load();
      instruction = "ALL CLEAR";

      activeStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment" },
        audio: true,
      });
      // Start continuous scanning loop
      scanEnvironment();
    } catch (err) {
      console.error("Camera access denied or unavailable", err);
    }
  });

  $: if (leftEyeVideo && activeStream) {
    leftEyeVideo.srcObject = activeStream;
    leftEyeVideo.play();
  }
  $: if (rightEyeVideo && activeStream) {
    rightEyeVideo.srcObject = activeStream;
    rightEyeVideo.play();
  }
  $: if (videoElement && activeStream) {
    videoElement.srcObject = activeStream;
    videoElement.play();
  }

  function scanEnvironment() {
    setInterval(async () => {
      if (!cocoModel || !videoElement || videoElement.readyState !== 4) return;

      const predictions = await cocoModel.detect(videoElement);

      // Look for specific objects in the frame
      const isPhoneDetected = predictions.some(
        (p: cocoSsd.DetectedObject) => p.class === "cell phone" && p.score > 0.5,
      );
      const isPersonOrPetDetected = predictions.some(
        (p: cocoSsd.DetectedObject) =>
          (p.class === "person" || p.class === "cat" || p.class === "dog") &&
          p.score > 0.5,
      );

      // Rule: Show QR only if cell phone is seen
      if (isPhoneDetected) {
        setState("STATE_EXCHANGING_IDENTITY");
        streamMode = "AUDIO_QR (Streaming only Audio + Captured QR)";
      }
      // Rule: Stream video/audio for people or pets if no phone covers it up
      else if (isPersonOrPetDetected) {
        if (
          currentState !== "STATE_SPEAKING" &&
          currentState !== "STATE_INSTRUCTING"
        ) {
          setState("STATE_LISTENING");
        }
        streamMode = "VIDEO_AUDIO (Streaming Small Video + Full Audio)";
      }
      // Rule: Otherwise, generic object or empty scene
      else {
        if (
          currentState !== "STATE_INSTRUCTING" &&
          currentState !== "STATE_SPEAKING"
        ) {
          setState("STATE_IDLE");
        }
        streamMode = "PICTURES (Sending Pictures/Snapshots)";
      }
    }, 2000); // Scan every 2 seconds matching PRD
  }
</script>

<main class="omni-app" class:dreaming={isSocialPage}>
  {#if !isSocialPage}
    <div class="camera-feed-bg">
      <video
        bind:this={videoElement}
        class="hidden-vision-source"
        autoplay
        playsinline
        muted
      ></video>
      <div class="hud-overlay">
        <!-- Status indicator for the requested Context-Aware Streaming -->
        <div class="streaming-status">
          [Mode: {streamMode}]
        </div>
        {#if currentState === "STATE_INSTRUCTING"}
          <h1 class="instruction-text">{instruction}</h1>
        {/if}

        <div class="bot-face state-{currentState} emotion-{emotion}">
          <div class="cute-eyes">
            <!-- Wrapping pupils in a white sclera for cuteness -->
            <div class="sclera">
              <div
                class="eye left-eye"
                style="transform: translate({eyeOffsetX}px, {eyeOffsetY}px) scaleY({blink
                  ? 0.1
                  : 1});"
              >
                <video
                  bind:this={leftEyeVideo}
                  class="reflection-cam"
                  autoplay
                  playsinline
                  muted
                ></video>
              </div>
            </div>
            <div class="sclera">
              <div
                class="eye right-eye"
                style="transform: translate({eyeOffsetX}px, {eyeOffsetY}px) scaleY({blink
                  ? 0.1
                  : 1});"
              >
                <video
                  bind:this={rightEyeVideo}
                  class="reflection-cam"
                  autoplay
                  playsinline
                  muted
                ></video>
              </div>
            </div>
          </div>

          <!-- Expressive Mouth Element -->
          <div
            class="mouth"
            class:qr-active={currentState === "STATE_EXCHANGING_IDENTITY"}
          >
            {#if currentState === "STATE_EXCHANGING_IDENTITY"}
              <img src={qrCodeUrl} alt="Identity QR Code" class="qr-code" />
            {/if}
          </div>
        </div>

        <div class="controls">
          <button on:click={() => setState("STATE_IDLE")}>Idle</button>
          <button on:click={() => setState("STATE_LISTENING")}>Listen</button>
          <button on:click={() => setState("STATE_THINKING")}>Think</button>
          <button on:click={() => setState("STATE_SPEAKING")}>Speak</button>
          <button on:click={() => setState("STATE_INSTRUCTING")}
            >Instruct</button
          >
          <button on:click={() => setState("STATE_EXCHANGING_IDENTITY")}
            >Exchange ID</button
          >
          <a href="/social" target="_blank" class="button-link">Dream Feed</a>
        </div>
      </div>
    </div>
  {:else}
    <div class="dream-feed">
      <h1>OmniBot Social Network</h1>
      <p>
        NanoBanana2 (Watercolor Painting Style) Generated Images feed goes
        here...
      </p>

      <div class="gallery">
        {#if discoveries.length === 0}
          <p>No dreams generated yet.</p>
        {/if}
        {#each discoveries as dream}
          <div class="card">
            <div class="watercolor-frame">
              <!-- Dynamically generating the NanoBanana2 dream via simple prompt -->
              <img
                src={`https://image.pollinations.ai/prompt/watercolor%20painting%20style%20${encodeURIComponent(dream.description)}?width=400&height=300&nologo=true`}
                alt="Watercolor Dream"
                class="watercolor-effect"
              />
            </div>
            <p><strong>{dream.timestamp}</strong> - {dream.type}</p>
            <p>{dream.description}</p>
            {#if dream.lat && dream.lng}
              <div class="map-frame">
                <iframe
                  title="Memory Location Map"
                  width="100%"
                  height="150"
                  style="border:0;"
                  loading="lazy"
                  src={`https://maps.google.com/maps?q=${dream.lat},${dream.lng}&z=14&output=embed`}
                >
                </iframe>
              </div>
            {/if}
          </div>
        {/each}
      </div>
    </div>
  {/if}
</main>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
    background: #000;
    font-family: "Space Mono", monospace; /* Stencil style / Cyber minimalist */
    color: #00ffcc;
    overflow: hidden;
  }

  .omni-app {
    width: 100vw;
    height: 100dvh;
    display: flex;
    justify-content: center;
    align-items: center;
    position: relative;
  }

  .camera-feed-bg {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: radial-gradient(circle at center, #111, #000);
    z-index: 1;
  }

  .streaming-status {
    position: absolute;
    top: 2rem;
    left: 2rem;
    font-size: 0.8rem;
    color: #ff00ff;
    padding: 0.5rem;
    border: 1px solid #ff00ff;
    background: rgba(0, 0, 0, 0.5);
  }

  .hidden-vision-source {
    position: absolute;
    opacity: 0;
    pointer-events: none;
    width: 320px;
    height: 240px;
  }

  .hud-overlay {
    position: relative;
    z-index: 2;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    height: 100%;
  }

  .bot-face {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    transition: all 0.3s ease;
    gap: 40px; /* Space between eyes and mouth */
  }

  .cute-eyes {
    display: flex;
    gap: 40px;
    justify-content: center;
    align-items: center;
    width: 100%;
  }

  .mouth {
    width: 40px;
    height: 6px;
    background-color: #00ffcc;
    border-radius: 10px;
    border: none;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    display: flex;
    justify-content: center;
    align-items: center;
    overflow: hidden; /* Keep the QR code contained if needed */
  }

  /* Emotions Base Gestures (applied mostly when neutral state) */
  .emotion-happy .mouth {
    width: 60px;
    height: 25px;
    background-color: transparent;
    border: 6px solid #00ffcc;
    border-top: transparent;
    border-left: transparent;
    border-right: transparent;
    border-radius: 0 0 50px 50px;
    transform: translateY(-5px);
  }

  .emotion-sad .mouth {
    width: 60px;
    height: 20px;
    background-color: transparent;
    border: 6px solid #00ffcc;
    border-bottom: transparent;
    border-left: transparent;
    border-right: transparent;
    border-radius: 50px 50px 0 0;
    transform: translateY(10px);
  }

  .emotion-surprise .mouth {
    width: 30px;
    height: 40px;
    border-radius: 50%;
    background-color: #00ffcc; /* filled O shape */
  }

  .emotion-neutral .mouth {
    width: 40px;
    height: 6px;
    border-radius: 10px;
    background-color: #00ffcc;
    border: none;
  }

  .sclera {
    width: 130px;
    height: 160px;
    background-color: #fff;
    border-radius: 50%;
    display: flex;
    justify-content: center;
    align-items: center;
    box-shadow:
      inset 0 0 20px rgba(0, 0, 0, 0.5),
      0 0 20px #00ffcc;
    overflow: hidden;
  }

  .eye {
    width: 90px;
    height: 110px;
    background-color: #000;
    border-radius: 50%;
    position: relative;
    overflow: hidden;
    transition: transform 0.15s cubic-bezier(0.4, 0, 0.2, 1);
    display: flex;
    justify-content: center;
    align-items: center;
    /* Removed background-color: #000 so video shows easily if transparent */
  }

  .reflection-cam {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
    opacity: 0.8; /* Eye reflection opacity */
    z-index: 10;
  }

  /* State Animations on the Sclera/Eyes container */
  .state-STATE_IDLE .sclera {
    animation: pulse 3s infinite ease-in-out;
  }
  .state-STATE_LISTENING .sclera {
    box-shadow:
      inset 0 0 10px rgba(0, 0, 0, 0.5),
      0 0 30px #00ffcc,
      0 0 60px #00ffcc;
  }
  .state-STATE_SPEAKING .sclera {
    animation: pulse 0.5s infinite alternate;
  }
  .state-STATE_INSTRUCTING .sclera {
    box-shadow:
      inset 0 0 10px rgba(0, 0, 0, 0.5),
      0 0 20px #ffcc00;
  }
  /* Remove the eye animation for identity exchange so eyes stay stable */

  /* State Overrides for the mouth */
  .state-STATE_SPEAKING .mouth {
    border: 5px solid #00ffcc;
    background-color: #00ffcc;
    border-radius: 50%;
    animation: talk 0.2s infinite alternate;
  }

  .state-STATE_THINKING .mouth {
    width: 20px;
    height: 6px;
    border-radius: 10px;
    background-color: #00ffcc;
    border: none;
    transform: translateX(20px) rotate(15deg); /* Hmm... offset expression */
  }

  .state-STATE_INSTRUCTING .mouth {
    width: 70px;
    height: 25px;
    background-color: transparent;
    border: 6px solid #ffcc00; /* Yellow */
    border-bottom-color: #ffcc00;
    border-radius: 0 0 50px 50px;
    border-top: transparent;
    border-left: transparent;
    border-right: transparent;
  }

  @keyframes talk {
    0% {
      height: 10px;
      width: 40px;
      border-radius: 20px;
    }
    100% {
      height: 50px;
      width: 30px;
      border-radius: 50%;
    }
  }

  .state-STATE_EXCHANGING_IDENTITY .mouth {
    width: 140px;
    height: 140px;
    border-radius: 20px;
    background: rgba(0, 255, 204, 0.1);
    border: 4px solid #00ffcc;
    animation: openQRMouth 0.5s forwards;
  }

  @keyframes openQRMouth {
    0% {
      transform: scaleY(1);
      border-radius: 50%;
      width: 40px;
      height: 6px;
    }
    100% {
      transform: scaleY(1);
      border-radius: 20px;
      width: 140px;
      height: 140px;
      background: rgba(0, 255, 204, 0.1);
      border: 2px solid #00ffcc;
    }
  }

  .qr-code {
    width: 100%;
    height: 100%;
    object-fit: contain;
    animation: revealQR 0.5s ease 0.3s forwards;
    opacity: 0;
  }

  @keyframes pulse {
    0% {
      transform: scale(1);
      opacity: 0.8;
    }
    50% {
      transform: scale(1.1);
      opacity: 1;
    }
    100% {
      transform: scale(1);
      opacity: 0.8;
    }
  }
  @keyframes lookAround {
    0%,
    100% {
      transform: translateX(0);
    }
    25% {
      transform: translateX(-20px);
    }
    75% {
      transform: translateX(20px);
    }
  }
  @keyframes speak {
    0% {
      transform: scaleY(0.8);
    }
    100% {
      transform: scaleY(1.3);
    }
  }
  @keyframes mouthOpen {
    0% {
      transform: scaleY(1);
      border-radius: 50%;
    }
    100% {
      transform: scaleY(1.5);
      border-radius: 20px;
      background: rgba(0, 255, 204, 0.1);
      border: 2px solid #00ffcc;
    }
  }
  @keyframes revealQR {
    to {
      opacity: 1;
    }
  }

  .controls {
    position: absolute;
    bottom: 2rem;
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    justify-content: center;
  }

  button {
    background: transparent;
    border: 1px solid #00ffcc;
    color: #00ffcc;
    padding: 0.5rem 1rem;
    cursor: pointer;
    font-family: inherit;
  }

  button:hover,
  .button-link:hover {
    background: #00ffcc;
    color: #000;
  }

  .button-link {
    display: inline-block;
    background: transparent;
    border: 1px solid #00ffcc;
    color: #00ffcc;
    padding: 0.5rem 1rem;
    cursor: pointer;
    font-family: inherit;
    text-decoration: none;
    font-size: 13.3333px; /* Match button font size */
    box-sizing: border-box;
  }

  /* Dream Feed */
  .dream-feed {
    width: 100%;
    height: 100%;
    padding: 2rem;
    box-sizing: border-box;
    overflow-y: auto;
  }

  .gallery {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1rem;
    margin-top: 2rem;
  }

  .card {
    border: 1px solid #333;
    padding: 1rem;
    background: #111;
  }

  .watercolor-frame {
    width: 100%;
    border-radius: 4px;
    overflow: hidden;
    background: #fff; /* Paper-like background for watercolor */
    padding: 0.5rem;
    box-sizing: border-box;
  }

  .watercolor-effect {
    width: 100%;
    height: auto;
    border-radius: 2px;
    /* Simulate a low-detailed watercolor look via CSS filters */
    filter: saturate(1.5) contrast(1.1) brightness(1.1) blur(0.5px) sepia(0.2);
    mix-blend-mode: multiply;
  }

  .card p {
    margin-top: 1rem;
    color: #aaa;
  }

  .map-frame {
    margin-top: 1rem;
    border-radius: 4px;
    overflow: hidden;
    border: 1px solid #333;
  }
</style>
