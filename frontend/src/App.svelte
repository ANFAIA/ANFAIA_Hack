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
  let feedLoading = true;
  let feedError = "";

  // In dev, use relative URLs so Vite proxy forwards to localhost:8000.
  // In production, set VITE_BACKEND_URL to the deployed backend.
  const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "";

  async function fetchDreams() {
    feedError = "";
    try {
      const resp = await fetch(`${BACKEND_URL}/discoveries`);
      if (resp.ok) {
        const payload = await resp.json();
        discoveries = payload.data ?? [];
      } else {
        feedError = `Server error ${resp.status}`;
      }
    } catch (err) {
      feedError = "Cannot reach backend. Is the server running?";
      console.error("Failed to load dreams:", err);
    } finally {
      feedLoading = false;
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
  let started = false; // guards media init behind a user tap (required on mobile)

  onMount(async () => {
    if (isSocialPage) {
      await fetchDreams();
      // Auto-refresh every 8 s so new dreams appear without a reload
      setInterval(fetchDreams, 8000);
      return;
    }

    startEyeBehaviors();

    // Pre-load the heavy TF model while waiting for the user tap so startup
    // feels instant once they interact.
    instruction = "INITIALIZING AI...";
    cocoSsd.load().then((model) => {
      cocoModel = model;
      instruction = started ? "ALL CLEAR" : "TAP TO START";
    });
  });

  // Called from the tap-to-start overlay — runs inside a user gesture so
  // getUserMedia + video.play() are always permitted on iOS/Android.
  async function startCamera() {
    started = true;
    if (cocoModel) instruction = "ALL CLEAR";

    try {
      activeStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment", width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: true,
      });

      // Assign srcObject and play all videos inside the gesture callback
      await Promise.all([
        assignAndPlay(videoElement, activeStream),
        assignAndPlay(leftEyeVideo, activeStream),
        assignAndPlay(rightEyeVideo, activeStream),
      ]);

      scanEnvironment();
    } catch (err) {
      console.error("Camera access denied or unavailable", err);
      instruction = "CAMERA UNAVAILABLE";
    }
  }

  async function assignAndPlay(el: HTMLVideoElement | undefined, stream: MediaStream) {
    if (!el) return;
    el.srcObject = stream;
    el.muted = true;          // required for autoplay policy
    el.playsInline = true;    // required on iOS
    try {
      await el.play();
    } catch (e) {
      console.warn("video.play() failed:", e);
    }
  }

  // Reactive assignments: only assign if the element doesn't already have this
  // stream (avoids AbortError from interrupting an in-progress load).
  $: if (leftEyeVideo && activeStream && leftEyeVideo.srcObject !== activeStream)
    assignAndPlay(leftEyeVideo, activeStream);
  $: if (rightEyeVideo && activeStream && rightEyeVideo.srcObject !== activeStream)
    assignAndPlay(rightEyeVideo, activeStream);
  $: if (videoElement && activeStream && videoElement.srcObject !== activeStream)
    assignAndPlay(videoElement, activeStream);

  // ─── Snapshot capture ────────────────────────────────────────────────────────
  let _scanCanvas: HTMLCanvasElement | null = null;

  function captureFrame(): Blob | null {
    if (!videoElement || videoElement.readyState < 2) return null;
    if (!_scanCanvas) _scanCanvas = document.createElement("canvas");
    _scanCanvas.width = videoElement.videoWidth || 320;
    _scanCanvas.height = videoElement.videoHeight || 240;
    const ctx = _scanCanvas.getContext("2d");
    if (!ctx) return null;
    ctx.drawImage(videoElement, 0, 0, _scanCanvas.width, _scanCanvas.height);
    const dataUrl = _scanCanvas.toDataURL("image/jpeg", 0.8);
    const [header, b64] = dataUrl.split(",");
    const mime = header.match(/:(.*?);/)![1];
    const binary = atob(b64);
    const arr = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) arr[i] = binary.charCodeAt(i);
    return new Blob([arr], { type: mime });
  }

  // ─── Object-change-triggered capture ─────────────────────────────────────────
  // A frame is only sent to the backend when COCO-SSD detects a different set
  // of objects than the previous scan — no timer, no redundant captures.
  let lastDream = "";
  let prevObjectKey = "";   // sorted class names of last detected objects
  let dreamPending = false; // prevent overlapping requests

  async function dreamIfObjectsChanged(predictions: cocoSsd.DetectedObject[]) {
    // Use ALL detected classes (lower threshold 0.3) to build the scene key.
    // Including "person" means a new person appearing also triggers a capture.
    // Gemini Vision will describe the full scene richly regardless of class.
    const key = predictions
      .filter(p => p.score > 0.3)
      .map(p => p.class)
      .sort()
      .join(",");

    dbg.sceneKey = key || "(none)"; dbg = dbg;

    if (!key) return;                  // nothing at all visible
    if (key === prevObjectKey) return; // scene unchanged
    if (dreamPending) return;          // request in flight

    prevObjectKey = key;
    console.log("[OmniBot] Scene changed →", key);

    const blob = captureFrame();
    if (!blob) { console.warn("[OmniBot] captureFrame returned null"); return; }

    dreamPending = true;
    const form = new FormData();
    form.append("file", blob, "frame.jpg");
    form.append("lat", "0");
    form.append("lng", "0");
    form.append("scene_labels", key); // COCO-SSD labels as fallback for Gemini vision

    try {
      console.log("[OmniBot] Posting to /bot/discover …");
      const resp = await fetch(`${BACKEND_URL}/bot/discover`, { method: "POST", body: form });
      if (!resp.ok) { console.error("[OmniBot] /bot/discover status:", resp.status); return; }
      const data = await resp.json();
      if (data.saved) {
        lastDream = data.description ?? "";
        dbg.dreams++; dbg = dbg;
        console.log("[OmniBot] Dream saved:", lastDream);
        if (currentState !== "STATE_LISTENING" && currentState !== "STATE_SPEAKING") {
          setState("STATE_THINKING");
          streamMode = `DREAMING: ${lastDream.slice(0, 35)}`;
        }
      }
    } catch (e) {
      console.error("[OmniBot] Dream capture error:", e);
    } finally {
      dreamPending = false;
    }
  }

  // ─── Cooldown (brain instruction only) ───────────────────────────────────────
  let lastInstructMs = 0;
  const INSTRUCT_COOLDOWN = 10_000;

  async function fetchBrainInstruction() {
    const now = Date.now();
    if (now - lastInstructMs < INSTRUCT_COOLDOWN) return;
    lastInstructMs = now;

    try {
      const resp = await fetch(`${BACKEND_URL}/bot/instruct`);
      if (resp.ok) {
        const data = await resp.json();
        instruction = data.instruction ?? "SCANNING...";
      }
    } catch (e) {
      console.error("[OmniBot] Brain instruction error:", e);
    }
  }

  // ─── Autonomous environment scan loop ────────────────────────────────────────
  function scanEnvironment() {
    setInterval(async () => {
      if (!cocoModel || !videoElement || videoElement.readyState !== 4) return;

      const predictions = await cocoModel.detect(videoElement);

      // Log everything COCO-SSD sees above 0.3
      const labels = predictions.filter(p => p.score > 0.3).map(p => `${p.class}(${p.score.toFixed(2)})`);
      dbg.detected = labels.join(", ") || "(none)"; dbg = dbg;

      const isPhoneDetected = predictions.some(
        (p: cocoSsd.DetectedObject) => p.class === "cell phone" && p.score > 0.5,
      );
      const isPersonOrPetDetected = predictions.some(
        (p: cocoSsd.DetectedObject) =>
          (p.class === "person" || p.class === "cat" || p.class === "dog") &&
          p.score > 0.5,
      );
      const hasAnyObject = predictions.some(
        (p: cocoSsd.DetectedObject) => p.score > 0.5,
      );

      // Always check for new objects regardless of other states
      dreamIfObjectsChanged(predictions);

      if (isPhoneDetected) {
        // ① Another phone → open mouth, show QR, pause live chat
        if (isStreaming) stopLiveSession();
        setState("STATE_EXCHANGING_IDENTITY");
        streamMode = "QR IDENTITY EXCHANGE";

      } else if (isPersonOrPetDetected) {
        // ② Person or pet → auto-start live audio conversation
        streamMode = "LIVE AUDIO CHAT";
        if (!isStreaming) startLiveSession();
        // state (LISTENING / SPEAKING) managed by live session events

      } else if (hasAnyObject) {
        // ③ Object only → show thinking state
        if (isStreaming) stopLiveSession();
        if (currentState !== "STATE_THINKING") setState("STATE_THINKING");
        streamMode = "SCANNING OBJECT...";

      } else {
        // ④ Nothing detected → ask brain for exploration instruction
        if (isStreaming) stopLiveSession();
        prevObjectKey = ""; // reset so next appearance triggers a new capture
        setState("STATE_INSTRUCTING");
        streamMode = "EXPLORING...";
        fetchBrainInstruction();
      }
    }, 2000); // scan every 2 s
  }

  // ─── Gemini Live API (WebSocket) ────────────────────────────────────────────
  // Build WS URL: use Vite proxy (/ws) in dev, full URL in production
  // In dev, use window.location.host (includes :5173) so the request goes
  // through the Vite proxy → ws://localhost:8000/ws on the backend.
  // In production, derive from VITE_BACKEND_URL.
  const WS_URL = import.meta.env.VITE_BACKEND_URL
    ? `${import.meta.env.VITE_BACKEND_URL.replace(/^http/, "ws")}/ws`
    : `ws://${window.location.host}/ws`;

  // Gemini outputs PCM at 24 kHz; we send PCM at 16 kHz
  const GEMINI_OUTPUT_SAMPLE_RATE = 24000;
  const GEMINI_INPUT_SAMPLE_RATE = 16000;

  let liveWs: WebSocket | null = null;
  let audioCtx: AudioContext | null = null;
  let scriptProcessor: ScriptProcessorNode | null = null;
  let isStreaming = false;
  let liveError = "";
  let liveReconnectAt = 0; // timestamp after which reconnection is allowed

  // Playback queue so audio chunks play sequentially
  let audioQueue: AudioBuffer[] = [];
  let isPlayingAudio = false;
  let nextPlayTime = 0;

  // ─── Debug state (visible on screen) ─────────────────────────────────────────
  let showDebug = false;
  let dbg = {
    ws: "DISCONNECTED",        // WebSocket connection state
    audioCtx: "—",             // AudioContext.state
    chunksRx: 0,               // audio chunks received from Gemini
    micTx: 0,                  // mic packets sent to Gemini
    lastMsg: "—",              // last WS message type received
    detected: "—",             // current COCO-SSD detections
    sceneKey: "—",             // current object key
    dreams: 0,                 // total dreams saved
  };
  function dbgTick() {
    if (audioCtx) dbg.audioCtx = audioCtx.state;
    dbg = dbg; // trigger Svelte reactivity
  }
  setInterval(dbgTick, 500);

  function downsampleTo16k(input: Float32Array, fromRate: number): Float32Array {
    if (fromRate === GEMINI_INPUT_SAMPLE_RATE) return input;
    const ratio = fromRate / GEMINI_INPUT_SAMPLE_RATE;
    const out = new Float32Array(Math.floor(input.length / ratio));
    for (let i = 0; i < out.length; i++) {
      out[i] = input[Math.floor(i * ratio)];
    }
    return out;
  }

  async function startLiveSession() {
    if (liveWs) return;
    if (Date.now() < liveReconnectAt) return; // still in cooldown
    liveError = "";
    setState("STATE_THINKING");

    liveWs = new WebSocket(WS_URL);
    liveWs.binaryType = "arraybuffer";
    dbg.ws = "CONNECTING"; dbg = dbg;

    liveWs.onopen = async () => {
      console.log("[OmniBot] WS open →", WS_URL);
      dbg.ws = "CONNECTED"; dbg = dbg;
      setState("STATE_LISTENING");
      await startAudioCapture();
      isStreaming = true;
    };

    liveWs.onmessage = async (event: MessageEvent) => {
      try {
        const msg = JSON.parse(event.data as string);
        dbg.lastMsg = msg.type ?? "?"; dbg = dbg;
        console.log("[OmniBot] WS msg:", msg.type, msg.type === "audio" ? `(${(msg.data?.length ?? 0)} chars b64)` : "");
        if (msg.type === "audio") {
          dbg.chunksRx++; dbg = dbg;
          setState("STATE_SPEAKING");
          enqueueAudio(msg.data as string);
        } else if (msg.type === "turn_complete") {
          if (audioQueue.length === 0 && !isPlayingAudio) {
            setState("STATE_LISTENING");
          }
        } else if (msg.type === "error") {
          liveError = msg.message ?? "Unknown error";
          console.error("[OmniBot] Gemini error:", liveError);
          stopLiveSession();
        }
      } catch {
        // Non-JSON message — ignore
      }
    };

    liveWs.onclose = (ev) => {
      console.log("[OmniBot] WS closed", ev.code, ev.reason);
      dbg.ws = "DISCONNECTED"; dbg = dbg;
      cleanupAudio();
      isStreaming = false;
      liveWs = null;
      // Back-off: wait 3 s before allowing reconnect (avoids hammering on 1011 timeout)
      liveReconnectAt = Date.now() + 3000;
      setState("STATE_IDLE");
    };

    liveWs.onerror = (err) => {
      console.error("[OmniBot] WS error:", err);
      dbg.ws = "ERROR"; dbg = dbg;
      liveError = "Connection failed. Is the backend running?";
      stopLiveSession();
    };
  }

  async function startAudioCapture() {
    const micStream =
      activeStream ??
      (await navigator.mediaDevices.getUserMedia({ audio: true }));

    // Create AudioContext at browser native rate; we'll downsample manually.
    audioCtx = new AudioContext();
    // Resume immediately — AudioContext created outside a user gesture starts suspended.
    await audioCtx.resume();

    const source = audioCtx.createMediaStreamSource(micStream);
    scriptProcessor = audioCtx.createScriptProcessor(4096, 1, 1);
    source.connect(scriptProcessor);

    // Silent gain keeps the graph alive without looping mic audio to speakers.
    const silentGain = audioCtx.createGain();
    silentGain.gain.value = 0;
    scriptProcessor.connect(silentGain);
    silentGain.connect(audioCtx.destination);

    console.log("[OmniBot] AudioContext sampleRate:", audioCtx.sampleRate, "state:", audioCtx.state);

    scriptProcessor.onaudioprocess = (e: AudioProcessingEvent) => {
      // Don't send mic audio while bot is speaking — prevents echo feedback.
      if (!liveWs || liveWs.readyState !== WebSocket.OPEN || isPlayingAudio) return;
      const raw = e.inputBuffer.getChannelData(0);
      const pcm32 = downsampleTo16k(raw, audioCtx!.sampleRate);
      const pcm16 = new Int16Array(pcm32.length);
      for (let i = 0; i < pcm32.length; i++) {
        pcm16[i] = Math.max(-32768, Math.min(32767, Math.round(pcm32[i] * 32767)));
      }
      liveWs.send(pcm16.buffer);
      dbg.micTx++;
    };
  }

  function enqueueAudio(base64Data: string) {
    if (!audioCtx) return;

    // Decode base64 → raw bytes → Int16 PCM (Gemini output: 24 kHz, mono)
    const binary = atob(base64Data);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);

    const pcm16 = new Int16Array(bytes.buffer);
    // Create an AudioBuffer tagged at 24 kHz; AudioContext resamples automatically.
    const buf = audioCtx.createBuffer(1, pcm16.length, GEMINI_OUTPUT_SAMPLE_RATE);
    const ch = buf.getChannelData(0);
    for (let i = 0; i < pcm16.length; i++) ch[i] = pcm16[i] / 32768;

    audioQueue.push(buf);
    if (!isPlayingAudio) schedulePlayback();
  }

  function schedulePlayback() {
    if (!audioCtx || audioQueue.length === 0) {
      isPlayingAudio = false;
      if (isStreaming) setState("STATE_LISTENING");
      return;
    }

    isPlayingAudio = true;
    const buf = audioQueue.shift()!;

    const play = () => {
      const src = audioCtx!.createBufferSource();
      src.buffer = buf;
      src.connect(audioCtx!.destination);
      const startAt = Math.max(audioCtx!.currentTime, nextPlayTime);
      src.start(startAt);
      nextPlayTime = startAt + buf.duration;
      src.onended = () => schedulePlayback();
    };

    // AudioContext may be suspended if created outside a user-gesture context.
    if (audioCtx.state === "suspended") {
      audioCtx.resume().then(play);
    } else {
      play();
    }
  }

  function cleanupAudio() {
    scriptProcessor?.disconnect();
    scriptProcessor = null;
    audioCtx?.close();
    audioCtx = null;
    audioQueue = [];
    isPlayingAudio = false;
    nextPlayTime = 0;
  }

  function stopLiveSession() {
    liveWs?.close();
    liveWs = null;
    cleanupAudio();
    isStreaming = false;
    setState("STATE_IDLE");
  }
</script>

<main class="omni-app" class:dreaming={isSocialPage}>
  {#if !isSocialPage}
    {#if !started}
      <button class="tap-overlay" on:click={startCamera} aria-label="Start OmniBot">
        <span class="tap-ring"></span>
        <span class="tap-label">TAP TO ACTIVATE</span>
      </button>
    {/if}
    <div class="camera-feed-bg">
      <video
        bind:this={videoElement}
        class="hidden-vision-source"
        autoplay
        playsinline
        muted
      ></video>
      <div class="hud-overlay">
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

        <!-- Debug panel (tap corner to toggle) -->
        <button class="debug-toggle" on:click={() => (showDebug = !showDebug)}>
          {showDebug ? "✕" : "⚙"}
        </button>
        {#if showDebug}
        <div class="debug-panel">
          <div>Mode: <b>{streamMode}</b></div>
          <div>WS: <b>{dbg.ws}</b></div>
          <div>AudioCtx: <b>{dbg.audioCtx}</b></div>
          <div>Chunks RX: <b>{dbg.chunksRx}</b></div>
          <div>Mic TX: <b>{dbg.micTx}</b></div>
          <div>Seen: <b>{dbg.detected}</b></div>
          <div>Key: <b>{dbg.sceneKey}</b></div>
          <div>Dreams: <b>{dbg.dreams}</b></div>
          {#if liveError}<div style="color:#f44">ERR: {liveError}</div>{/if}
        </div>
        {/if}

        <div class="controls">
          <a href="/social" target="_blank" class="button-link">Dream Feed</a>
        </div>
      </div>
    </div>
  {:else}
    <div class="dream-feed">
      <h1>OmniBot Social Network</h1>

      {#if feedLoading}
        <p class="feed-status">Loading dreams…</p>
      {:else if feedError}
        <p class="feed-status feed-status--error">{feedError}</p>
        <button class="retry-btn" on:click={fetchDreams}>Retry</button>
      {:else if discoveries.length === 0}
        <p class="feed-status">No dreams generated yet. Point the bot at something interesting!</p>
      {:else}
        <p class="feed-count">{discoveries.length} dream{discoveries.length === 1 ? "" : "s"} — refreshing every 8 s</p>
      {/if}

      <div class="gallery">
        {#each discoveries as dream (dream.id)}
          <div class="card">
            <div class="watercolor-frame">
              {#if dream.original_image_url}
                <div class="image-half">
                  <img
                    src={dream.original_image_url}
                    alt="Original Capture"
                    class="original-effect"
                    on:error={(e) => { (e.currentTarget as HTMLImageElement).style.display = "none"; }}
                  />
                  <p class="image-label">Camera Reality</p>
                </div>
              {/if}
              <div class="image-half" class:full-width={!dream.original_image_url}>
                <img
                  src={dream.image_url
                    ? dream.image_url
                    : `https://image.pollinations.ai/prompt/watercolor%20painting%20style%20${encodeURIComponent(dream.description)}?width=400&height=300&nologo=true`}
                  alt="Watercolor Dream"
                  class="watercolor-effect"
                  on:error={(e) => {
                    const img = e.currentTarget as HTMLImageElement;
                    if (!img.src.includes("pollinations")) {
                      img.src = `https://image.pollinations.ai/prompt/watercolor%20painting%20style%20${encodeURIComponent(dream.description)}?width=400&height=300&nologo=true`;
                    }
                  }}
                />
                <p class="image-label">Bot's Dream</p>
              </div>
            </div>
            <p class="card-meta"><strong>{dream.timestamp}</strong> — {dream.type}</p>
            <p class="card-desc">{dream.description}</p>
            {#if dream.lat && dream.lng}
              <div class="map-frame">
                <iframe
                  title="Memory Location Map"
                  width="100%"
                  height="150"
                  style="border:0;"
                  loading="lazy"
                  src={`https://maps.google.com/maps?q=${dream.lat},${dream.lng}&z=14&output=embed`}
                ></iframe>
              </div>
            {/if}
          </div>
        {/each}
      </div>
    </div>
  {/if}
</main>

<style>
  .tap-overlay {
    position: fixed;
    inset: 0;
    z-index: 100;
    background: rgba(0, 0, 0, 0.92);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    gap: 2rem;
    border: none;
    cursor: pointer;
    touch-action: manipulation; /* prevent double-tap zoom on mobile */
  }

  .tap-ring {
    display: block;
    width: 120px;
    height: 120px;
    border-radius: 50%;
    border: 3px solid #00ffcc;
    animation: tapPulse 1.5s infinite ease-in-out;
  }

  .tap-label {
    font-family: "Space Mono", monospace;
    color: #00ffcc;
    font-size: 1.1rem;
    letter-spacing: 0.15em;
  }

  @keyframes tapPulse {
    0%, 100% { transform: scale(1); opacity: 0.6; box-shadow: 0 0 10px #00ffcc; }
    50% { transform: scale(1.15); opacity: 1; box-shadow: 0 0 40px #00ffcc; }
  }

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
    align-items: center;
  }

  .debug-toggle {
    position: absolute;
    top: 1rem;
    right: 1rem;
    z-index: 10;
    background: transparent;
    border: 1px solid #00ffcc44;
    color: #00ffcc88;
    font-size: 1rem;
    width: 2rem;
    height: 2rem;
    padding: 0;
    cursor: pointer;
    line-height: 1;
  }

  .debug-toggle:hover {
    border-color: #00ffcc;
    color: #00ffcc;
    background: transparent;
  }

  .debug-panel {
    position: absolute;
    top: 3.5rem;
    right: 1rem;
    font-size: 0.7rem;
    line-height: 1.6;
    color: #00ffcc;
    background: rgba(0, 0, 0, 0.7);
    border: 1px solid #00ffcc44;
    padding: 0.5rem 0.8rem;
    font-family: "Space Mono", monospace;
    pointer-events: none;
  }

  .live-error {
    color: #ff4444;
    font-size: 0.7rem;
    border: 1px solid #ff4444;
    padding: 0.3rem 0.6rem;
    background: rgba(255, 68, 68, 0.1);
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
    display: flex;
    gap: 10px;
  }

  .image-half {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .image-half.full-width {
    width: 100%;
  }

  .original-effect {
    width: 100%;
    border-radius: 2px;
    height: 100%;
    object-fit: cover;
  }

  .image-label {
    font-size: 0.7rem;
    color: #666;
    margin-top: 5px;
    text-align: center;
  }

  .watercolor-effect {
    width: 100%;
    height: 100%;
    object-fit: cover;
    border-radius: 2px;
    /* Simulate a low-detailed watercolor look via CSS filters */
    filter: saturate(1.5) contrast(1.1) brightness(1.1) blur(0.5px) sepia(0.2);
    mix-blend-mode: multiply;
  }

  .feed-status {
    color: #aaa;
    margin-top: 1rem;
    font-size: 0.9rem;
  }

  .feed-status--error {
    color: #f44;
  }

  .feed-count {
    color: #00ffcc55;
    font-size: 0.75rem;
    margin-top: 0.5rem;
  }

  .retry-btn {
    margin-top: 0.5rem;
    background: transparent;
    border: 1px solid #f44;
    color: #f44;
    padding: 0.4rem 1rem;
    cursor: pointer;
    font-family: inherit;
  }

  .card-meta {
    margin-top: 0.75rem;
    color: #888;
    font-size: 0.75rem;
  }

  .card-desc {
    margin-top: 0.25rem;
    color: #aaa;
    font-size: 0.85rem;
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
