// Honor the OS reduced-motion preference: skip decorative animation,
// show final states immediately. Applies to particle canvas, reveals,
// counters, terminal typing, spotlight, tilt and floating particles.
const REDUCED = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

// Full-page particle network background
(function () {
  if (REDUCED) return;
  const canvas = document.createElement('canvas');
  canvas.style.cssText = 'position:fixed;inset:0;z-index:0;pointer-events:none;';
  document.body.insertBefore(canvas, document.body.firstChild);
  const ctx = canvas.getContext('2d');

  const COLORS = [
    [99,102,241],[139,92,246],[34,211,238],[167,139,250],[129,140,248]
  ];
  const COUNT = 90, LINK = 160, PUSH = 120;
  let W, H, pts, mx = -9999, my = -9999;

  function resize() {
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }

  function init() {
    pts = Array.from({ length: COUNT }, () => {
      const c = COLORS[Math.floor(Math.random() * COLORS.length)];
      return {
        x: Math.random() * W, y: Math.random() * H,
        vx: (Math.random() - 0.5) * 0.45,
        vy: (Math.random() - 0.5) * 0.45,
        r: Math.random() * 1.6 + 0.5,
        c, a: Math.random() * 0.35 + 0.25,
        phase: Math.random() * Math.PI * 2,
      };
    });
  }

  function draw() {
    ctx.clearRect(0, 0, W, H);
    for (let i = 0; i < pts.length - 1; i++) {
      for (let j = i + 1; j < pts.length; j++) {
        const dx = pts[i].x - pts[j].x, dy = pts[i].y - pts[j].y;
        const d2 = dx * dx + dy * dy;
        if (d2 < LINK * LINK) {
          const t = 1 - Math.sqrt(d2) / LINK;
          const c = pts[i].c;
          ctx.beginPath();
          ctx.moveTo(pts[i].x, pts[i].y);
          ctx.lineTo(pts[j].x, pts[j].y);
          ctx.strokeStyle = `rgba(${c[0]},${c[1]},${c[2]},${+(t * 0.26).toFixed(3)})`;
          ctx.lineWidth = t * 1.1;
          ctx.stroke();
        }
      }
    }
    pts.forEach(p => {
      p.phase += 0.018;
      const pulse = 0.82 + Math.sin(p.phase) * 0.18;
      const r = p.r * pulse;
      const g = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, r * 5.5);
      g.addColorStop(0, `rgba(${p.c[0]},${p.c[1]},${p.c[2]},${+(p.a * 0.45).toFixed(3)})`);
      g.addColorStop(1, `rgba(${p.c[0]},${p.c[1]},${p.c[2]},0)`);
      ctx.beginPath(); ctx.arc(p.x, p.y, r * 5.5, 0, Math.PI * 2);
      ctx.fillStyle = g; ctx.fill();
      ctx.beginPath(); ctx.arc(p.x, p.y, r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${p.c[0]},${p.c[1]},${p.c[2]},${+p.a.toFixed(3)})`;
      ctx.fill();
    });
  }

  function update() {
    pts.forEach(p => {
      const dx = p.x - mx, dy = p.y - my;
      const d  = Math.sqrt(dx * dx + dy * dy);
      if (d < PUSH && d > 0) {
        const f = (PUSH - d) / PUSH * 0.85;
        p.vx += dx / d * f; p.vy += dy / d * f;
      }
      p.vx *= 0.985; p.vy *= 0.985;
      const spd = Math.sqrt(p.vx * p.vx + p.vy * p.vy);
      if (spd > 2.4) { p.vx = p.vx / spd * 2.4; p.vy = p.vy / spd * 2.4; }
      p.x += p.vx; p.y += p.vy;
      if (p.x < -12) p.x = W + 12; if (p.x > W + 12) p.x = -12;
      if (p.y < -12) p.y = H + 12; if (p.y > H + 12) p.y = -12;
    });
  }

  function loop() { update(); draw(); requestAnimationFrame(loop); }

  document.addEventListener('mousemove', e => { mx = e.clientX; my = e.clientY; });
  window.addEventListener('resize', () => { resize(); init(); }, { passive: true });
  resize(); init(); loop();
})();

// Scroll-reveal
const _obs = new IntersectionObserver(
  entries => entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible'); }),
  { threshold: 0.08 }
);
if (REDUCED) {
  document.querySelectorAll('.fade-up').forEach(el => el.classList.add('visible'));
} else {
  document.querySelectorAll('.fade-up').forEach(el => _obs.observe(el));
}

// Hamburger (index.html only)
const _hamburger = document.getElementById('hamburger');
const _mobileMenu = document.getElementById('mobileMenu');
if (_hamburger && _mobileMenu) {
  _hamburger.addEventListener('click', () => {
    _hamburger.classList.toggle('open');
    _mobileMenu.classList.toggle('open');
  });
}

// Scroll progress bar
const _progressBar = document.createElement('div');
_progressBar.className = 'scroll-progress';
document.body.prepend(_progressBar);
window.addEventListener('scroll', () => {
  const pct = window.scrollY / (document.documentElement.scrollHeight - window.innerHeight) * 100;
  _progressBar.style.width = Math.min(pct, 100) + '%';
}, { passive: true });

// Cursor spotlight
if (!REDUCED) {
  const _spotlight = document.createElement('div');
  _spotlight.className = 'cursor-spotlight';
  document.body.appendChild(_spotlight);
  document.addEventListener('mousemove', e => {
    _spotlight.style.left = e.clientX + 'px';
    _spotlight.style.top  = e.clientY + 'px';
  });
}

// Floating upward particles
if (!REDUCED) (function() {
  for (let i = 0; i < 22; i++) {
    const p = document.createElement('div');
    p.className = 'particle';
    const sz = (Math.random() * 2 + 0.8).toFixed(1);
    const color = Math.random() > 0.5
      ? `rgba(99,102,241,${(Math.random()*0.25+0.1).toFixed(2)})`
      : `rgba(139,92,246,${(Math.random()*0.25+0.1).toFixed(2)})`;
    p.style.cssText =
      `width:${sz}px;height:${sz}px;` +
      `left:${(Math.random()*100).toFixed(1)}vw;` +
      `background:${color};` +
      `--drift:${((Math.random()-0.5)*120).toFixed(0)}px;` +
      `animation-duration:${(Math.random()*18+14).toFixed(1)}s;` +
      `animation-delay:-${(Math.random()*22).toFixed(1)}s;`;
    document.body.appendChild(p);
  }
})();

// Float hero terminal card (index.html only)
setTimeout(() => {
  const heroRight = document.querySelector('.hero-right');
  if (heroRight) heroRight.classList.add('float-card');
}, 1600);

// Counter animation on stat numbers
function _countUp(el) {
  const raw = el.textContent.trim();
  const num = parseInt(raw);
  const suffix = raw.slice(num.toString().length);
  if (isNaN(num)) return;
  const dur = 1400, t0 = performance.now();
  el.textContent = '0' + suffix;
  const tick = now => {
    const p = Math.min((now - t0) / dur, 1);
    const ease = 1 - Math.pow(1 - p, 3);
    el.textContent = Math.round(ease * num) + suffix;
    if (p < 1) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}
const _counterObs = new IntersectionObserver(entries => {
  entries.forEach(e => {
    if (e.isIntersecting) { _countUp(e.target); _counterObs.unobserve(e.target); }
  });
}, { threshold: 0.7 });
if (!REDUCED) {
  document.querySelectorAll('.hero-stat-val, .stat-val').forEach(el => _counterObs.observe(el));
}

// Terminal typing animation (index.html only)
if (!REDUCED) (function() {
  const body = document.querySelector('.terminal-body');
  if (!body) return;
  const kids = [...body.children];
  kids.forEach(k => {
    k.style.opacity = '0';
    k.style.transform = 'translateY(5px)';
    k.style.transition = 'none';
  });
  const cursor = document.createElement('span');
  cursor.className = 't-cursor';
  if (kids[0]) kids[0].appendChild(cursor);
  let delay = 300;
  kids.forEach(k => {
    const d = delay;
    setTimeout(() => {
      k.style.transition = 'opacity 0.32s ease, transform 0.32s ease';
      k.style.opacity = '1';
      k.style.transform = 'translateY(0)';
    }, d);
    delay += k.classList.contains('t-line') ? 230 : 90;
  });
  setTimeout(() => cursor.remove(), delay + 600);
})();

// 3D tilt on glass cards
if (!REDUCED) document.querySelectorAll('.glass').forEach(card => {
  card.addEventListener('mousemove', e => {
    const r = card.getBoundingClientRect();
    const x = (e.clientX - r.left) / r.width - 0.5;
    const y = (e.clientY - r.top)  / r.height - 0.5;
    card.style.transform = `perspective(900px) rotateY(${(x*7).toFixed(2)}deg) rotateX(${(-y*7).toFixed(2)}deg) translateY(-4px)`;
  });
  card.addEventListener('mouseleave', () => { card.style.transform = ''; });
});
