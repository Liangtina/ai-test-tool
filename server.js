const http = require('http');

const PORT = 3000;

function getHTML(serverTime) {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Hello World</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      background: #0d0d1a;
      font-family: 'Segoe UI', system-ui, sans-serif;
      overflow: hidden;
    }

    /* ── Starfield ── */
    #starfield {
      position: fixed;
      inset: 0;
      width: 100%;
      height: 100%;
      pointer-events: none;
      z-index: 0;
    }

    /* ── Card ── */
    .card {
      position: relative;
      z-index: 1;
      text-align: center;
      padding: 3rem 4rem;
      border-radius: 24px;
      background: rgba(255,255,255,0.04);
      border: 1px solid rgba(255,255,255,0.12);
      backdrop-filter: blur(12px);
      box-shadow: 0 0 80px rgba(100,80,255,0.25), 0 0 0 1px rgba(255,255,255,0.05);
      animation: float 6s ease-in-out infinite;
    }
    @keyframes float {
      0%, 100% { transform: translateY(0); }
      50%       { transform: translateY(-14px); }
    }

    /* ── Greeting text ── */
    h1 {
      font-size: clamp(2.5rem, 8vw, 5rem);
      font-weight: 800;
      letter-spacing: -0.03em;
      background: linear-gradient(135deg, #a78bfa, #60a5fa, #34d399, #a78bfa);
      background-size: 300% 300%;
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      animation: shimmer 5s linear infinite;
    }
    @keyframes shimmer {
      0%   { background-position: 0% 50%; }
      100% { background-position: 300% 50%; }
    }

    /* ── Subtitle ── */
    .subtitle {
      margin-top: 0.6rem;
      font-size: 1rem;
      color: rgba(255,255,255,0.45);
      letter-spacing: 0.1em;
      text-transform: uppercase;
    }

    /* ── Divider ── */
    .divider {
      width: 60px;
      height: 2px;
      margin: 1.6rem auto;
      background: linear-gradient(90deg, #a78bfa, #60a5fa);
      border-radius: 2px;
      opacity: 0.7;
    }

    /* ── Time block ── */
    .time-block {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
    }
    .time-label {
      font-size: 0.7rem;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: rgba(255,255,255,0.3);
    }
    #clock {
      font-size: clamp(1.6rem, 4vw, 2.4rem);
      font-weight: 700;
      font-variant-numeric: tabular-nums;
      color: #e0e7ff;
      text-shadow: 0 0 20px rgba(167,139,250,0.6);
    }
    #date-line {
      font-size: 0.85rem;
      color: rgba(255,255,255,0.4);
    }

    /* ── Pulse ring around clock ── */
    .pulse-ring {
      position: relative;
      display: inline-block;
    }
    .pulse-ring::after {
      content: '';
      position: absolute;
      inset: -10px;
      border-radius: 16px;
      border: 1px solid rgba(167,139,250,0.4);
      animation: ring-pulse 2s ease-out infinite;
    }
    @keyframes ring-pulse {
      0%   { opacity: 0.8; transform: scale(1); }
      100% { opacity: 0;   transform: scale(1.08); }
    }

    /* ── Server time badge ── */
    .server-badge {
      margin-top: 1.5rem;
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      padding: 0.3rem 0.75rem;
      border-radius: 999px;
      background: rgba(52,211,153,0.1);
      border: 1px solid rgba(52,211,153,0.25);
      font-size: 0.72rem;
      color: #6ee7b7;
      letter-spacing: 0.06em;
    }
    .dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: #34d399;
      animation: blink 1.4s ease-in-out infinite;
    }
    @keyframes blink {
      0%, 100% { opacity: 1; }
      50%       { opacity: 0.2; }
    }
  </style>
</head>
<body>

  <!-- Starfield (canvas-based zoom) -->
  <canvas id="starfield"></canvas>

  <div class="card">
    <h1>Hello, World!</h1>
    <p class="subtitle">Node.js · HTTP · No dependencies</p>

    <div class="divider"></div>

    <div class="time-block">
      <span class="time-label">Current time</span>
      <div class="pulse-ring">
        <div id="clock">--:--:--</div>
      </div>
      <div id="date-line"></div>
    </div>

    <div class="server-badge">
      <div class="dot"></div>
      Server booted at ${serverTime}
    </div>
  </div>

  <script>
    /* ── Hyperspace starfield ── */
    (function() {
      const canvas = document.getElementById('starfield');
      const ctx = canvas.getContext('2d');
      const STAR_COUNT = 200;
      const SPEED = 0.0075;      // fractional distance per frame
      const TRAIL_ALPHA = 0.18;  // motion-blur fade per frame
      const MIN_DIST = 0.02;     // min starting distance from center (0–1)

      let W, H, cx, cy, stars;

      function mkStar() {
        // Random angle, random starting distance from center
        const angle = Math.random() * Math.PI * 2;
        const dist  = MIN_DIST + Math.random() * (0.5 - MIN_DIST);
        return {
          angle,
          dist,
          speed: 0.6 + Math.random() * 0.8,  // per-star speed multiplier
          size:  0.5 + Math.random() * 1.2,
          bright: 0.5 + Math.random() * 0.5
        };
      }

      function resize() {
        W = canvas.width  = window.innerWidth;
        H = canvas.height = window.innerHeight;
        cx = W / 2;
        cy = H / 2;
      }

      function init() {
        resize();
        stars = Array.from({ length: STAR_COUNT }, mkStar);
      }

      function drawFrame() {
        // Fade existing content to create motion-blur streaks
        ctx.fillStyle = 'rgba(13,13,26,' + TRAIL_ALPHA + ')';
        ctx.fillRect(0, 0, W, H);

        for (let i = 0; i < stars.length; i++) {
          const st = stars[i];

          // Advance outward — accelerate as distance grows
          st.dist += SPEED * st.speed * (0.4 + st.dist * 3);

          // Convert polar coords to screen coords
          const x = cx + Math.cos(st.angle) * st.dist * Math.max(W, H);
          const y = cy + Math.sin(st.angle) * st.dist * Math.max(W, H);

          // Size grows with distance
          const r = st.size * (0.5 + st.dist * 4);

          // Opacity grows with distance
          const alpha = Math.min(1, st.bright * (st.dist * 5));

          if (x < -20 || x > W + 20 || y < -20 || y > H + 20) {
            // Recycle off-screen star back to center region
            stars[i] = mkStar();
          } else {
            ctx.beginPath();
            ctx.arc(x, y, Math.max(0.3, r), 0, Math.PI * 2);
            ctx.fillStyle = 'rgba(255,255,255,' + alpha.toFixed(2) + ')';
            ctx.fill();
          }
        }

        requestAnimationFrame(drawFrame);
      }

      window.addEventListener('resize', resize);
      init();
      drawFrame();
    })();

    /* ── Live clock ── */
    const DAYS   = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
    const MONTHS = ['January','February','March','April','May','June',
                    'July','August','September','October','November','December'];

    function pad(n) { return String(n).padStart(2, '0'); }

    function tick() {
      const now = new Date();
      const h = pad(now.getHours()), m = pad(now.getMinutes()), s = pad(now.getSeconds());
      document.getElementById('clock').textContent = h + ':' + m + ':' + s;
      document.getElementById('date-line').textContent =
        DAYS[now.getDay()] + ', ' + MONTHS[now.getMonth()] + ' ' + now.getDate() + ', ' + now.getFullYear();
    }
    tick();
    setInterval(tick, 1000);
  </script>
</body>
</html>`;
}

const server = http.createServer((req, res) => {
  if (req.url !== '/' && req.url !== '/index.html') {
    res.writeHead(404, { 'Content-Type': 'text/plain' });
    res.end('Not found');
    return;
  }

  const serverTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  const html = getHTML(serverTime);

  res.writeHead(200, {
    'Content-Type': 'text/html; charset=utf-8',
    'Content-Length': Buffer.byteLength(html),
  });
  res.end(html);
});

server.listen(PORT, () => {
  console.log('Hello World server running at http://localhost:' + PORT);
});
