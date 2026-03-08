<script lang="ts">
  import { onMount } from 'svelte';

  // Routing
  const isSocialPage = window.location.pathname === '/social';

  type BotState = 'STATE_IDLE' | 'STATE_LISTENING' | 'STATE_THINKING' | 'STATE_SPEAKING' | 'STATE_INSTRUCTING' | 'STATE_EXCHANGING_IDENTITY';
  let currentState: BotState = 'STATE_IDLE';

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
      const resp = await fetch('http://localhost:8000/discoveries');
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

  onMount(async () => {
    if (isSocialPage) {
      fetchDreams();
      return;
    }
    
    try {
      activeStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' }, audio: true });
      // Start continuous scanning loop
      scanEnvironment();
    } catch (err) {
      console.error("Camera access denied or unavailable", err);
    }
  });

  $: if (videoElement && activeStream) { videoElement.srcObject = activeStream; videoElement.play(); }
  $: if (leftEyeVideo && activeStream) { leftEyeVideo.srcObject = activeStream; leftEyeVideo.play(); }
  $: if (rightEyeVideo && activeStream) { rightEyeVideo.srcObject = activeStream; rightEyeVideo.play(); }

  function scanEnvironment() {
    setInterval(() => {
      // In a real app, this would use Gemini Vision / MLKit bounding boxes.
      // Mocking the detection logic Based on the PRD rules:
      const randomDetection = Math.random();
      
      if (randomDetection > 0.9) {
        // Detect another robot / Phone
        setState('STATE_EXCHANGING_IDENTITY');
        streamMode = 'AUDIO_QR (Streaming only Audio + Captured QR)';
      } else if (randomDetection > 0.7) {
        // Detect human / pet
        setState('STATE_LISTENING'); // or STATE_THINKING
        streamMode = 'VIDEO_AUDIO (Streaming Small Video + Full Audio)';
      } else {
        // Default: Detect generic object
        if (currentState !== 'STATE_INSTRUCTING' && currentState !== 'STATE_EXCHANGING_IDENTITY') {
             setState('STATE_IDLE');
        }
        streamMode = 'PICTURES (Sending Pictures/Snapshots)';
      }
      
    }, 4000); // Scan every 4 seconds
  }
</script>

<main class="omni-app" class:dreaming={isSocialPage}>
  {#if !isSocialPage}
    <div class="camera-feed-bg">
      <video bind:this={videoElement} class="real-camera" autoplay playsinline muted></video>
      <div class="hud-overlay">
        
        <!-- Status indicator for the requested Context-Aware Streaming -->
        <div class="streaming-status">
          [Mode: {streamMode}]
        </div>
        {#if currentState === 'STATE_INSTRUCTING'}
          <h1 class="instruction-text">{instruction}</h1>
        {/if}
        
        <div class="bot-face state-{currentState}">
          {#if currentState === 'STATE_EXCHANGING_IDENTITY'}
            <div class="bot-mouth-open">
              <img src={qrCodeUrl} alt="Identity QR Code" class="qr-code" />
            </div>
          {:else}
            <div class="cute-eyes">
              <div class="eye left-eye">
                <video bind:this={leftEyeVideo} class="reflection-cam" autoplay playsinline muted></video>
              </div>
              <div class="eye right-eye">
                <video bind:this={rightEyeVideo} class="reflection-cam" autoplay playsinline muted></video>
              </div>
            </div>
          {/if}
        </div>
        
        <div class="controls">
          <button on:click={() => setState('STATE_IDLE')}>Idle</button>
          <button on:click={() => setState('STATE_LISTENING')}>Listen</button>
          <button on:click={() => setState('STATE_THINKING')}>Think</button>
          <button on:click={() => setState('STATE_SPEAKING')}>Speak</button>
          <button on:click={() => setState('STATE_INSTRUCTING')}>Instruct</button>
          <button on:click={() => setState('STATE_EXCHANGING_IDENTITY')}>Exchange ID</button>
          <a href="/social" target="_blank" class="button-link">Dream Feed</a>
        </div>
      </div>
    </div>
  {:else}
    <div class="dream-feed">
      <h1>OmniBot Social Network</h1>
      <p>NanoBanana2 (Watercolor Painting Style) Generated Images feed goes here...</p>
      
      <div class="gallery">
        {#if discoveries.length === 0}
          <p>No dreams generated yet.</p>
        {/if}
        {#each discoveries as dream}
          <div class="card">
            <div class="watercolor-frame">
              <!-- Using the placeholder until NanoBanana2 returns the real image string from DB -->
              <img src="https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80" alt="Watercolor Dream" class="watercolor-effect" />
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
                  src={`https://maps.google.com/maps?q=${dream.lat},${dream.lng}&z=14&output=embed`}>
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
    font-family: 'Space Mono', monospace; /* Stencil style / Cyber minimalist */
    color: #00ffcc;
    overflow: hidden;
  }

  .omni-app {
    width: 100vw;
    height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
    position: relative;
  }

  .camera-feed-bg {
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background: radial-gradient(circle at center, #111, #000);
    z-index: 1;
  }

  .real-camera {
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 100%;
    object-fit: cover;
    opacity: 0.5; /* maintain cyber-aesthetic overlay */
    z-index: -1;
  }

  .streaming-status {
    position: absolute;
    top: 2rem;
    left: 2rem;
    font-size: 0.8rem;
    color: #ff00ff;
    padding: 0.5rem;
    border: 1px solid #ff00ff;
    background: rgba(0,0,0,0.5);
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

  .instruction-text {
    font-size: 3rem;
    color: #ffcc00; /* Yellow Warning/Caution */
    text-shadow: 0 0 10px #ffcc00;
    margin-bottom: 2rem;
  }

  .bot-face {
    width: 300px;
    height: 150px;
    display: flex;
    justify-content: center;
    align-items: center;
    transition: all 0.3s ease;
  }

  .cute-eyes {
    display: flex;
    gap: 40px;
    justify-content: center;
    align-items: center;
    width: 100%;
  }

  .eye {
    width: 70px;
    height: 90px;
    background-color: #000;
    border-radius: 50px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 0 15px #00ffcc;
    transition: all 0.3s ease;
    display: flex;
    justify-content: center;
    align-items: center;
  }

  .reflection-cam {
    width: 100%;
    height: 100%;
    object-fit: cover;
    opacity: 0.5; /* Eye reflection opacity */
    mix-blend-mode: screen;
  }

  /* State Animations */
  .state-STATE_IDLE .eye { animation: pulse 2s infinite ease-in-out; }
  .state-STATE_LISTENING .eye { box-shadow: 0 0 30px #00ffcc, 0 0 60px #00ffcc; transform: scale(1.2); }
  .state-STATE_THINKING .cute-eyes { animation: lookAround 2s infinite ease-in-out; }
  .state-STATE_SPEAKING .eye { animation: speak 0.2s infinite alternate; }
  .state-STATE_INSTRUCTING .eye { box-shadow: 0 0 20px #ffcc00; }
  .state-STATE_EXCHANGING_IDENTITY { animation: mouthOpen 0.5s forwards; }

  .bot-mouth-open {
    display: flex;
    justify-content: center;
    align-items: center;
    width: 100%;
    height: 100%;
    animation: revealQR 0.5s ease 0.3s forwards;
    opacity: 0;
  }

  .qr-code {
    width: 100px;
    height: 100px;
    border: 4px solid #00ffcc;
    border-radius: 8px;
  }
  
  @keyframes pulse {
    0% { transform: scale(1); opacity: 0.8; }
    50% { transform: scale(1.1); opacity: 1; }
    100% { transform: scale(1); opacity: 0.8; }
  }
  @keyframes lookAround {
    0%, 100% { transform: translateX(0); }
    25% { transform: translateX(-20px); }
    75% { transform: translateX(20px); }
  }
  @keyframes speak {
    0% { transform: scaleY(0.8); }
    100% { transform: scaleY(1.3); }
  }
  @keyframes mouthOpen {
    0% { transform: scaleY(1); border-radius: 50%; }
    100% { transform: scaleY(1.5); border-radius: 20px; background: rgba(0,255,204,0.1); border: 2px solid #00ffcc;}
  }
  @keyframes revealQR {
    to { opacity: 1; }
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
  
  button:hover, .button-link:hover { background: #00ffcc; color: #000; }

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
    width: 100%; height: 100%;
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
  
  .card p { margin-top: 1rem; color: #aaa; }

  .map-frame {
    margin-top: 1rem;
    border-radius: 4px;
    overflow: hidden;
    border: 1px solid #333;
  }
</style>
