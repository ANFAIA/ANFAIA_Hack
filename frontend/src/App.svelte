<script lang="ts">
  import { onMount } from 'svelte';

  // State Definitions (Antigravity Specs)
  type BotState = 'STATE_IDLE' | 'STATE_LISTENING' | 'STATE_THINKING' | 'STATE_SPEAKING' | 'STATE_INSTRUCTING' | 'STATE_DREAMING' | 'STATE_EXCHANGING_IDENTITY';
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
</script>

<main class="omni-app" class:dreaming={currentState === 'STATE_DREAMING'}>
  {#if currentState !== 'STATE_DREAMING'}
    <div class="camera-feed-bg">
      <!-- Future: Actual Camera Feed Stream mapped here -->
      <div class="hud-overlay">
        {#if currentState === 'STATE_INSTRUCTING'}
          <h1 class="instruction-text">{instruction}</h1>
        {/if}
        
        <div class="bot-face state-{currentState}">
          {#if currentState === 'STATE_EXCHANGING_IDENTITY'}
            <div class="bot-mouth-open">
              <img src={qrCodeUrl} alt="Identity QR Code" class="qr-code" />
            </div>
          {:else}
            <div class="core-eye" />
          {/if}
        </div>
        
        <div class="controls">
          <button on:click={() => setState('STATE_IDLE')}>Idle</button>
          <button on:click={() => setState('STATE_LISTENING')}>Listen</button>
          <button on:click={() => setState('STATE_THINKING')}>Think</button>
          <button on:click={() => setState('STATE_SPEAKING')}>Speak</button>
          <button on:click={() => setState('STATE_INSTRUCTING')}>Instruct</button>
          <button on:click={() => setState('STATE_EXCHANGING_IDENTITY')}>Exchange ID</button>
          <button on:click={() => setState('STATE_DREAMING')}>Dream</button>
        </div>
      </div>
    </div>
  {:else}
    <div class="dream-feed">
      <h1>Dream Gallery</h1>
      <p>NanoBanana2 (Watercolor Painting Style) Generated Images feed goes here...</p>
      <button on:click={() => setState('STATE_IDLE')}>Wake Up</button>
      
      <div class="gallery">
        <div class="card">
          <div class="watercolor-frame">
            <img src="https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80" alt="Watercolor Dream" class="watercolor-effect" />
          </div>
          <p>Met a cat. Stared at it for 3 minutes.</p>
        </div>
        <!-- More cards here... -->
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
    opacity: 0.9; 
    z-index: 1;
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
    width: 150px;
    height: 150px;
    border-radius: 50%;
    display: flex;
    justify-content: center;
    align-items: center;
    transition: all 0.3s ease;
  }

  .core-eye {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background: #00ffcc;
    box-shadow: 0 0 20px #00ffcc;
    transition: all 0.3s ease;
  }

  /* State Animations */
  .state-STATE_IDLE .core-eye { animation: pulse 2s infinite ease-in-out; }
  .state-STATE_LISTENING .core-eye { box-shadow: 0 0 50px #00ffcc, 0 0 100px #00ffcc; transform: scale(1.2); }
  .state-STATE_THINKING .core-eye { animation: rotate 0.5s infinite linear; border-top: 5px solid #fff; }
  .state-STATE_SPEAKING .core-eye { animation: speak 0.2s infinite alternate; }
  .state-STATE_INSTRUCTING .core-eye { background: #ffcc00; box-shadow: 0 0 20px #ffcc00; }
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
  @keyframes rotate {
    100% { transform: rotate(360deg); }
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
  
  button:hover { background: #00ffcc; color: #000; }

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
</style>
