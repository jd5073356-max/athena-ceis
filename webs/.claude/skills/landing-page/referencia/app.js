/* =========================================================
   CÓDIGO BETA — Scroll engine
   GSAP + ScrollTrigger + Lenis
   Module pattern. Vanilla ES6+.
   ========================================================= */

const CodigoBeta = (() => {
  /* ---------- State ---------- */
  const state = {
    lenis: null,
    video: null,
    videoReady: false,
    progressBar: null,
    rail: null,
    railTicks: [],
    sections: [],
    rafId: null,
    desiredTime: 0,
    currentTime: 0,
    seekInFlight: false,
    canvas: null,
    ctx: null,
  };

  /* ---------- Boot ---------- */
  const boot = () => {
    if (!window.gsap || !window.ScrollTrigger || !window.Lenis) {
      console.warn('Required libraries missing');
      return;
    }
    gsap.registerPlugin(ScrollTrigger);
    // GSAP's ticker can start asleep in some iframe / preview contexts even
    // with pending tweens; wake it once on boot to guarantee the first frame.
    gsap.ticker.wake();
    document.documentElement.classList.add('js-ready');

    state.video = document.getElementById('bgVideo');
    state.progressBar = document.getElementById('progressBar');
    state.rail = document.getElementById('rail');
    state.railTicks = state.rail ? [...state.rail.querySelectorAll('[data-rail]')] : [];
    state.sections = [...document.querySelectorAll('[data-rail-target]')];

    initLenis();
    prepareVideo();
    initHero();
    initRevealAnimations();
    initHighlights();
    initCharts();
    initRail();
    initDock();
    initProgressBar();
    initVideoScrub();
    initVideoFrameLoop();
    initCtaHover();
    initAI();
  };

  /* ---------- Lenis smooth scroll ----------
     We drive Lenis with its own requestAnimationFrame loop instead of
     tying it to gsap.ticker. The gsap-ticker trick is the canonical Lenis
     integration but, on some builds, parks the ticker at frame 1 because
     GSAP's auto-sleep races with our queued tweens, leaving the entire
     page frozen. Running our own RAF is simpler and bulletproof.
  -------------------------------------------------------------- */
  const initLenis = () => {
    const lenis = new Lenis({
      duration: 1.85,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      smoothWheel: true,
      wheelMultiplier: 0.7,
      touchMultiplier: 1.6,
    });
    state.lenis = lenis;

    lenis.on('scroll', ScrollTrigger.update);

    const raf = (time) => {
      lenis.raf(time);
      requestAnimationFrame(raf);
    };
    requestAnimationFrame(raf);
  };

  /* ---------- Prepare video for frame-accurate scrubbing ----------
     Some preview/hosted environments don't honor byte-range requests on
     the absolute serve URL, leaving the <video> element stuck in
     networkState=2 forever. We fetch the file as a Blob via the relative
     path (which carries the iframe's credentials cleanly) and assign a
     blob: URL, which is both bullet-proof and gives us instant seeking.
  ------------------------------------------------------------------- */
  const prepareVideo = () => {
    const v = state.video;
    if (!v) return;
    v.muted = true;
    v.playsInline = true;
    v.pause();
    if ('fastSeek' in v) v._supportsFast = true;

    const ready = () => {
      if (state.videoReady) return;
      state.videoReady = true;
      ScrollTrigger.refresh();
    };
    v.addEventListener('loadedmetadata', ready);
    v.addEventListener('canplay', ready);
    v.addEventListener('loadeddata', ready);
    v.addEventListener('durationchange', ready);

    // If metadata is already known (cached / fast network), the events
    // above may have fired before we attached. Check synchronously.
    if (isFinite(v.duration) && v.duration > 0) ready();

    // Async blob hydration — only swap if we get a real video MIME back.
    const originalSrc = v.getAttribute('src');
    if (originalSrc) {
      fetch(originalSrc, { credentials: 'same-origin' })
        .then((r) => {
          if (!r.ok) throw new Error('http ' + r.status);
          const ct = r.headers.get('content-type') || '';
          if (!ct.startsWith('video')) throw new Error('not video: ' + ct);
          return r.blob();
        })
        .then((blob) => {
          const url = URL.createObjectURL(blob);
          v.removeAttribute('src');
          v.src = url;
          v.load();
        })
        .catch((err) => {
          console.warn('[video] blob hydration skipped:', err.message);
        });
    }
  };

  /* ---------- Hero entrance ---------- */
  const initHero = () => {
    const titleLines = document.querySelectorAll('.hero__title .split-line > span');
    const sup = document.querySelector('.hero__sup');
    const manifesto = document.querySelector('.hero__manifesto');
    const scrollMeta = document.querySelector('.hero__scroll');

    // Title rises with stagger — JS owns the hidden state so CSS can't
    // poison GSAP's transform parser with a translateY(110%) computed value.
    gsap.set(titleLines, { yPercent: 110, y: 0 });
    const tl = gsap.timeline({ defaults: { ease: 'expo.out' } });

    tl.to(titleLines, {
      yPercent: 0,
      duration: 1.3,
      stagger: 0.12,
      delay: 0.15,
    });

    if (sup) {
      gsap.set(sup, { opacity: 0, y: 14 });
      tl.to(sup, { opacity: 1, y: 0, duration: 0.8 }, 0.05);
    }
    if (manifesto) {
      gsap.set(manifesto, { opacity: 0, filter: 'blur(18px)', y: 20 });
      tl.to(manifesto, { opacity: 1, filter: 'blur(0px)', y: 0, duration: 1.1 }, 0.6);
    }
    if (scrollMeta) {
      gsap.set(scrollMeta, { opacity: 0, y: 14 });
      tl.to(scrollMeta, { opacity: 1, y: 0, duration: 0.7 }, 0.9);
    }
  };

  /* ---------- Reveal animations on scroll ----------
     Animation kinds: fade-blur, rise, scale-up, clip-circle
  ---------------------------------------------------- */
  const initRevealAnimations = () => {
    const nodes = document.querySelectorAll('[data-anim]');
    nodes.forEach((el) => {
      const kind = el.dataset.anim;
      const cfg = {
        scrollTrigger: {
          trigger: el,
          start: 'top 88%',
          end: 'top 35%',
          // play on enter (down), reverse on leave-back (up).
          // This makes every reveal replay each time you scroll past it.
          toggleActions: 'play none none reverse',
        },
        duration: 1.1,
        ease: 'expo.out',
      };

      switch (kind) {
        case 'fade-blur':
          gsap.to(el, { ...cfg, opacity: 1, filter: 'blur(0px)', y: 0 });
          break;
        case 'rise':
          gsap.to(el, { ...cfg, opacity: 1, y: 0, duration: 1.0 });
          break;
        case 'scale-up':
          gsap.to(el, { ...cfg, opacity: 1, scale: 1, y: 0, duration: 1.2 });
          break;
        case 'clip-circle':
          gsap.to(el, {
            ...cfg,
            clipPath: 'circle(140% at 50% 60%)',
            duration: 1.4,
            ease: 'expo.inOut',
          });
          break;
        case 'split-rise':
          gsap.to(el, { ...cfg, opacity: 1, y: 0 });
          break;
        default:
          gsap.to(el, { ...cfg, opacity: 1, y: 0 });
      }
    });

    // Stagger groups
    document.querySelectorAll('[data-anim-children]').forEach((parent) => {
      const kids = parent.querySelectorAll('[data-anim]');
      if (!kids.length) return;
      ScrollTrigger.create({
        trigger: parent,
        start: 'top 80%',
        end: 'top 30%',
        onEnter: () => {
          gsap.to(kids, {
            opacity: 1,
            y: 0,
            scale: 1,
            filter: 'blur(0px)',
            duration: 0.9,
            ease: 'expo.out',
            stagger: 0.08,
            overwrite: 'auto',
          });
        },
        onLeaveBack: () => {
          // Re-arm by snapping kids back to their hidden state
          kids.forEach((el) => {
            const kind = el.dataset.anim;
            const init = {};
            if (kind === 'fade-blur') Object.assign(init, { opacity: 0, filter: 'blur(18px)', y: 20 });
            else if (kind === 'rise') Object.assign(init, { opacity: 0, y: 60 });
            else if (kind === 'scale-up') Object.assign(init, { opacity: 0, scale: 0.92, y: 20 });
            else Object.assign(init, { opacity: 0, y: 40 });
            gsap.to(el, { ...init, duration: 0.5, ease: 'expo.in', overwrite: 'auto' });
          });
        },
      });
    });
  };

  /* ---------- Charts — animated drawing on scroll ---------- */
  const initCharts = () => {
    const charts = document.querySelectorAll('.chart');
    charts.forEach((c) => {
      ScrollTrigger.create({
        trigger: c,
        start: 'top 78%',
        end: 'top 25%',
        onEnter: () => c.classList.add('is-drawn'),
        onLeaveBack: () => c.classList.remove('is-drawn'),
        onEnterBack: () => c.classList.add('is-drawn'),
      });
    });
  };

  /* ---------- Rail index — active section ---------- */
  const initRail = () => {
    if (!state.railTicks.length) return;
    state.sections.forEach((sec) => {
      const idx = parseInt(sec.dataset.railTarget, 10);
      ScrollTrigger.create({
        trigger: sec,
        start: 'top 45%',
        end: 'bottom 45%',
        onToggle: (self) => {
          if (self.isActive) setActiveRail(idx);
        },
      });
    });
    setActiveRail(0);
  };

  const setActiveRail = (idx) => {
    state.railTicks.forEach((t) => {
      const i = parseInt(t.dataset.rail, 10);
      t.classList.toggle('is-active', i === idx);
    });
  };

  /* ---------- Dock — quick chapter navigation ---------- */
  const initDock = () => {
    const buttons = [...document.querySelectorAll('.dock__btn')];
    if (!buttons.length) return;

    const resolveTarget = (raw) => {
      if (raw === 'hero') return document.querySelector('.hero');
      // data-rail-target attribute on sections
      return document.querySelector(`[data-rail-target="${raw}"]`);
    };

    // Click → smooth scroll via Lenis
    buttons.forEach((btn) => {
      btn.addEventListener('click', () => {
        const el = resolveTarget(btn.dataset.dockTarget);
        if (!el) return;
        const top = el.getBoundingClientRect().top + window.scrollY - 20;
        if (state.lenis) {
          state.lenis.scrollTo(top, {
            duration: 1.8,
            easing: (t) => 1 - Math.pow(1 - t, 3),
          });
        } else {
          window.scrollTo({ top, behavior: 'smooth' });
        }
      });
    });

    // Active state — pick the dock entry whose target is closest above
    // the current scroll line.
    const setActive = () => {
      const probe = window.scrollY + window.innerHeight * 0.35;
      let activeBtn = null;
      let bestY = -Infinity;
      buttons.forEach((btn) => {
        const el = resolveTarget(btn.dataset.dockTarget);
        if (!el) return;
        const top = el.getBoundingClientRect().top + window.scrollY;
        if (top <= probe && top > bestY) {
          bestY = top;
          activeBtn = btn;
        }
      });
      buttons.forEach((btn) => btn.classList.toggle('is-active', btn === activeBtn));
    };

    if (state.lenis) state.lenis.on('scroll', setActive);
    window.addEventListener('scroll', setActive, { passive: true });
    window.addEventListener('resize', setActive);
    setActive();
  };

  /* ---------- Progress bar ---------- */
  const initProgressBar = () => {
    if (!state.progressBar) return;
    ScrollTrigger.create({
      start: 0,
      end: 'max',
      onUpdate: (self) => {
        state.progressBar.style.width = (self.progress * 100).toFixed(2) + '%';
      },
    });
  };

  /* ---------- Video scrub: keyframed by section ----------
     Instead of mapping the full document scroll linearly to the video,
     each section becomes an anchor with a target video time. The video
     interpolates between anchors based on the user's scroll position
     within the section. Effect: per-section pacing — long sections play
     the video slower, short ones faster, and the user always "arrives"
     at the chapter's intended moment.
  ----------------------------------------------------------- */
  const initVideoScrub = () => {
    const v = state.video;
    if (!v) return;

    // Build the keyframe table once we know the video duration AND the
    // page has fully laid out (after fonts + ScrollTrigger.refresh).
    const buildKeyframes = () => {
      if (!isFinite(v.duration) || v.duration <= 0) return;

      const anchorEls = [
        document.querySelector('.hero'),
        ...document.querySelectorAll('main > .section'),
        document.querySelector('.closing'),
      ].filter(Boolean);

      const n = anchorEls.length;
      if (n < 2) return;

      // Equal slice of the video per anchor — the LAST anchor lands at
      // duration, the FIRST at 0. Variable section heights cause the
      // playback speed between anchors to differ naturally.
      const keyframes = anchorEls.map((el, i) => ({
        y: 0,                                // recomputed below
        t: (i / (n - 1)) * v.duration,
      }));

      const refreshAnchorPositions = () => {
        for (let i = 0; i < n; i++) {
          const rect = anchorEls[i].getBoundingClientRect();
          keyframes[i].y = rect.top + window.scrollY;
        }
        // The very last anchor's playhead should land when its CENTER is on
        // screen, so the closing chapter actually plays through.
        const last = anchorEls[n - 1];
        keyframes[n - 1].y =
          last.getBoundingClientRect().top + window.scrollY +
          Math.max(0, last.offsetHeight - window.innerHeight * 0.6);
      };

      refreshAnchorPositions();
      window.addEventListener('resize', refreshAnchorPositions, { passive: true });
      // Re-measure once after any late layout shifts (font load, video load)
      setTimeout(refreshAnchorPositions, 400);

      state.keyframes = keyframes;
      state.keyframesReady = true;
    };

    // Watch the video for duration ready
    const tryBuild = () => {
      if (state.keyframesReady) return;
      if (isFinite(v.duration) && v.duration > 0) buildKeyframes();
    };
    v.addEventListener('loadedmetadata', tryBuild);
    v.addEventListener('durationchange', tryBuild);
    v.addEventListener('canplay', tryBuild);
    tryBuild();

    // Drive desiredTime from the actual scroll position via Lenis events.
    const updateFromScroll = (scrollY) => {
      const kf = state.keyframes;
      if (!kf || !kf.length) return;

      if (scrollY <= kf[0].y) { state.desiredTime = kf[0].t; return; }
      if (scrollY >= kf[kf.length - 1].y) {
        state.desiredTime = kf[kf.length - 1].t;
        return;
      }
      // Binary search for segment
      let lo = 0, hi = kf.length - 1;
      while (hi - lo > 1) {
        const mid = (lo + hi) >> 1;
        if (kf[mid].y <= scrollY) lo = mid;
        else hi = mid;
      }
      const a = kf[lo], b = kf[hi];
      const span = b.y - a.y;
      const ratio = span > 0 ? (scrollY - a.y) / span : 0;
      // Smoothstep within the segment so transitions across anchors
      // don't feel like a sharp speed change.
      const smooth = ratio * ratio * (3 - 2 * ratio);
      state.desiredTime = a.t + (b.t - a.t) * smooth;
    };

    // Tap into Lenis (smoothed scroll values) when available; fall back
    // to raw window.scrollY.
    if (state.lenis) {
      state.lenis.on('scroll', ({ scroll }) => updateFromScroll(scroll));
    }
    window.addEventListener('scroll', () => updateFromScroll(window.scrollY), { passive: true });
    updateFromScroll(window.scrollY);
  };

  /* ---------- Canvas-rendered scrub loop ----------
     Cinematic scrubbing requires that we don't seek the <video> element at
     all — seek latency between MP4 keyframes is what causes the visible
     stutter. Instead we pre-decode every frame ONCE into an ImageBitmap
     array, then scrub by INDEX. Drawing an ImageBitmap is a GPU-fast
     operation; the experience becomes pixel-perfect & deterministic.
  ----------------------------------------------------------------- */
  const initVideoFrameLoop = () => {
    const v = state.video;
    if (!v) return;

    // Build canvas overlay (matches the original .stage__video styling)
    const canvas = document.createElement('canvas');
    canvas.className = 'stage__canvas';
    Object.assign(canvas.style, {
      position: 'absolute',
      inset: '0',
      width: '100%',
      height: '100%',
      objectFit: 'cover',
      opacity: '0.85',
      filter: 'contrast(1.05) saturate(0.85)',
      zIndex: '1',
      pointerEvents: 'none',
      display: 'block',
    });
    const stage = document.querySelector('.stage');
    if (stage) stage.insertBefore(canvas, v.nextSibling);

    const ctx = canvas.getContext('2d', { alpha: false, desynchronized: true });
    state.canvas = canvas;
    state.ctx = ctx;

    // Hide the raw <video> — it stays in the DOM so it can decode
    v.style.opacity = '0';
    v.style.visibility = 'hidden';

    // ---- Frame store ----
    state.frames = [];        // [{ time, bitmap }]
    state.frameStoreReady = false;

    const sizeCanvas = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const rect = canvas.getBoundingClientRect();
      canvas.width = Math.round(rect.width * dpr);
      canvas.height = Math.round(rect.height * dpr);
    };

    const drawBitmap = (bm, alpha = 1) => {
      if (!bm) return;
      const cw = canvas.width, ch = canvas.height;
      const va = bm.width / bm.height;
      const ca = cw / ch;
      let dw, dh, dx, dy;
      if (ca > va) { dw = cw; dh = cw / va; dx = 0; dy = (ch - dh) / 2; }
      else { dh = ch; dw = ch * va; dy = 0; dx = (cw - dw) / 2; }
      const prevAlpha = ctx.globalAlpha;
      ctx.globalAlpha = alpha;
      try { ctx.drawImage(bm, dx, dy, dw, dh); } catch (_) {}
      ctx.globalAlpha = prevAlpha;
    };

    // First-frame paint as soon as we have one (before extraction completes)
    const paintRaw = () => {
      if (!v.videoWidth) return;
      const cw = canvas.width, ch = canvas.height;
      const va = v.videoWidth / v.videoHeight;
      const ca = cw / ch;
      let dw, dh, dx, dy;
      if (ca > va) { dw = cw; dh = cw / va; dx = 0; dy = (ch - dh) / 2; }
      else { dh = ch; dw = ch * va; dy = 0; dx = (cw - dw) / 2; }
      try { ctx.drawImage(v, dx, dy, dw, dh); } catch (_) {}
    };

    const onReady = () => {
      sizeCanvas();
      paintRaw();
      // Kick frame extraction once metadata + dimensions are known
      if (!state.frameStoreReady && !state._extracting) {
        state._extracting = true;
        if (state.lenis) state.lenis.stop();
        // Safety: if extraction takes longer than 20s, give up and unblock the page.
        const safety = setTimeout(() => {
          if (state.frameStoreReady) return;
          console.warn('[video] frame extraction timed out');
          hideLoader();
          if (state.lenis) state.lenis.start();
        }, 20000);
        extractFrames(v, updateLoader).then((frames) => {
          clearTimeout(safety);
          state.frames = frames;
          state.frameStoreReady = true;
          drawBitmap(frames[0]?.bitmap);
          hideLoader();
          if (state.lenis) state.lenis.start();
        }).catch((err) => {
          clearTimeout(safety);
          console.warn('[video] extraction failed:', err);
          hideLoader();
          if (state.lenis) state.lenis.start();
        });
      }
    };
    v.addEventListener('loadeddata', onReady);
    v.addEventListener('canplay', onReady);

    window.addEventListener('resize', () => {
      sizeCanvas();
      if (state.frameStoreReady && state.frames.length) {
        drawBitmap(state.frames[0].bitmap);
      } else {
        paintRaw();
      }
    }, { passive: true });

    // Helper — find two adjacent frames for sub-frame blending.
    // Returns { a, b, mix } where mix ∈ [0,1] is how much of `b` to blend in.
    const findFramePair = () => {
      const frames = state.frames;
      const n = frames.length;
      if (!n) return null;
      const t = state.currentTime;
      // Binary search for upper bound
      let lo = 0, hi = n - 1;
      while (lo < hi) {
        const mid = (lo + hi) >> 1;
        if (frames[mid].time < t) lo = mid + 1;
        else hi = mid;
      }
      // lo is the first frame with time >= t (or last frame)
      if (lo === 0) return { a: frames[0], b: frames[0], mix: 0 };
      const a = frames[lo - 1];
      const b = frames[lo];
      const span = b.time - a.time;
      const mix = span > 0 ? Math.min(1, Math.max(0, (t - a.time) / span)) : 0;
      return { a, b, mix };
    };

    // ---- Main RAF loop ----
    const TICK_EPS = 1 / 960;
    state.currentTime = 0;
    let lastT = -1;

    const tick = () => {
      state.rafId = requestAnimationFrame(tick);

      if (!isFinite(v.duration)) return;

      // Single, gentle lerp — Lenis already smooths the input and the
      // keyframe system already paces the playback; here we just damp the
      // remaining micro-jitter so blended frames don't strobe.
      const dt = state.desiredTime - state.currentTime;
      if (Math.abs(dt) > TICK_EPS) {
        state.currentTime += dt * 0.18;
      } else {
        state.currentTime = state.desiredTime;
      }
      if (state.currentTime < 0) state.currentTime = 0;
      if (state.currentTime > v.duration) state.currentTime = v.duration;

      if (state.frameStoreReady && state.currentTime !== lastT) {
        const pair = findFramePair();
        if (pair) {
          // Sub-frame blending: at slow speeds this is what gives the
          // "between frames" smoothness — the video appears continuous
          // instead of stepping discretely.
          drawBitmap(pair.a.bitmap, 1);
          if (pair.mix > 0.001) {
            drawBitmap(pair.b.bitmap, pair.mix);
          }
        }
        lastT = state.currentTime;
      }
    };
    state.rafId = requestAnimationFrame(tick);

    if (v.videoWidth) onReady();
  };

  /* ---------- Loader helpers ---------- */
  const updateLoader = (pct) => {
    const bar = document.getElementById('loaderBar');
    const txt = document.getElementById('loaderPct');
    const frame = document.getElementById('loaderFrame');
    if (bar) bar.style.transform = `scaleX(${pct})`;
    if (txt) txt.textContent = Math.round(pct * 100);
    if (frame) {
      const v = state.video;
      const total = (v && isFinite(v.duration)) ? Math.round(v.duration * 24) : 192;
      frame.textContent = String(Math.round(pct * total)).padStart(3, '0');
    }
  };
  const hideLoader = () => {
    const el = document.getElementById('loader');
    if (el) {
      el.classList.add('is-hidden');
      // Refresh ScrollTrigger after the loader unblocks layout
      setTimeout(() => ScrollTrigger.refresh(), 50);
    }
  };

  /* ---------- Frame extraction ----------
     Plays the video once at high speed; uses requestVideoFrameCallback
     when available to capture every decoded frame at native cadence.
     Falls back to a polled timeupdate sampler if not.
  --------------------------------------------- */
  const extractFrames = (v, onProgress) => {
    return new Promise(async (resolve) => {
      // Downscale capture so we don't blow memory on long videos.
      const MAX_W = 854;
      const scale = Math.min(1, MAX_W / v.videoWidth);
      const w = Math.round(v.videoWidth * scale);
      const h = Math.round(v.videoHeight * scale);

      const off = document.createElement('canvas');
      off.width = w; off.height = h;
      const offCtx = off.getContext('2d', { alpha: false });

      const frames = [];
      const pending = [];
      const reportProgress = () => {
        if (onProgress && isFinite(v.duration) && v.duration > 0) {
          onProgress(Math.min(1, v.currentTime / v.duration));
        }
      };

      const capture = (mediaTime) => {
        offCtx.drawImage(v, 0, 0, w, h);
        const p = createImageBitmap(off).then((bm) => {
          frames.push({ time: mediaTime, bitmap: bm });
        });
        pending.push(p);
      };

      const finish = async () => {
        try { v.pause(); } catch (_) {}
        v.playbackRate = 1;
        await Promise.all(pending);
        frames.sort((a, b) => a.time - b.time);
        if (onProgress) onProgress(1);
        resolve(frames);
      };

      v.muted = true;
      v.currentTime = 0;
      v.playbackRate = 8;

      if ('requestVideoFrameCallback' in v) {
        const onVF = (now, meta) => {
          capture(meta.mediaTime);
          reportProgress();
          if (v.ended || meta.mediaTime >= v.duration - 0.02) {
            finish();
          } else {
            v.requestVideoFrameCallback(onVF);
          }
        };
        v.addEventListener('ended', finish, { once: true });
        try {
          await v.play();
          v.requestVideoFrameCallback(onVF);
        } catch (e) {
          // play() blocked — fall back to seek polling
          fallbackSeekPoll();
        }
      } else {
        fallbackSeekPoll();
      }

      // Fallback: deterministic seek-and-grab at ~30fps
      async function fallbackSeekPoll() {
        const fps = 30;
        const step = 1 / fps;
        const total = Math.ceil(v.duration * fps);
        for (let i = 0; i < total; i++) {
          const t = Math.min(v.duration, i * step);
          await new Promise((res) => {
            const onSeeked = () => { v.removeEventListener('seeked', onSeeked); res(); };
            v.addEventListener('seeked', onSeeked);
            try { v.currentTime = t; } catch (_) { res(); }
          });
          capture(t);
          if (onProgress) onProgress((i + 1) / total);
        }
        finish();
      }
    });
  };

  /* ---------- Highlight wipe — ink for italic words, replays on scroll ---------- */
  const initHighlights = () => {
    const selectors = [
      '.heading em',
      '.pull em',
      '.lead em',
      '.hero__title em',
      '.closing__title em',
      '.mark',
      '.under',
    ];
    const emphases = document.querySelectorAll(selectors.join(','));
    emphases.forEach((el) => {
      let stamp = null;
      ScrollTrigger.create({
        trigger: el,
        start: 'top 85%',
        end: 'top 30%',
        onEnter: () => {
          // Small stagger so the highlight follows the reveal
          stamp = setTimeout(() => el.classList.add('is-lit'), 250);
        },
        onLeaveBack: () => {
          if (stamp) { clearTimeout(stamp); stamp = null; }
          el.classList.remove('is-lit');
        },
        onEnterBack: () => {
          stamp = setTimeout(() => el.classList.add('is-lit'), 150);
        },
        onLeave: () => {
          // Don't remove when scrolling past — only on the way back up.
        },
      });
    });
  };

  /* ---------- CTA — subtle 3D tilt on pointer ---------- */
  const initCtaHover = () => {
    document.querySelectorAll('.cta, .calendar').forEach((el) => {
      let rafId = null;
      const onMove = (e) => {
        const rect = el.getBoundingClientRect();
        const x = (e.clientX - rect.left) / rect.width - 0.5;
        const y = (e.clientY - rect.top) / rect.height - 0.5;
        if (rafId) cancelAnimationFrame(rafId);
        rafId = requestAnimationFrame(() => {
          el.style.transform = `perspective(800px) rotateX(${(-y * 4).toFixed(2)}deg) rotateY(${(x * 6).toFixed(2)}deg) translateY(-2px)`;
        });
      };
      const onLeave = () => {
        if (rafId) cancelAnimationFrame(rafId);
        el.style.transform = '';
      };
      el.addEventListener('pointermove', onMove);
      el.addEventListener('pointerleave', onLeave);
    });
  };

  /* ---------- AI Assistant ---------- */
  const initAI = () => {
    const fab = document.getElementById('aiFab');
    const panel = document.getElementById('aiPanel');
    const closeBtn = document.getElementById('aiClose');
    const body = document.getElementById('aiBody');
    const form = document.getElementById('aiForm');
    const input = document.getElementById('aiInput');
    const sendBtn = document.getElementById('aiSend');
    const suggestions = document.getElementById('aiSuggestions');
    if (!fab || !panel) return;

    const SYSTEM = `Eres el asistente conversacional de Código Beta, un estudio pequeño de tres ingenieros con oficina en Bogotá, Colombia, especializado en software a medida.

Identidad y tono:
- Hablas en español, con voz editorial, calma, segura. Frases cortas. Sin emojis. Sin marketing florido.
- Te refieres al equipo como "nosotros" o "el taller". Eres directo y honesto.
- Si no sabes algo específico (precios exactos, fechas), invitas a agendar una llamada o escribir por WhatsApp.

Lo que ofrecemos:
- Software a medida — NO plantillas, NO landings genéricas.
- Tres áreas principales: plataformas logísticas, ciberseguridad y auditoría, orquestación en la nube, gestión interna sensible.
- Proceso de tres fases: Planos (planeación + arquitectura, 20% del esfuerzo), Cimientos (ingeniería, 55%), Acabados (pulido y despliegue, 25%).
- Pagos: 50% al iniciar, 50% al entregar. Sin costos ocultos. El código fuente queda del cliente.
- Mantenimiento opcional con cuota mensual fija.

Lo que NO hacemos:
- No reescribimos código heredado enredado.
- No vendemos horas, vendemos soluciones.
- No hacemos proyectos express ni parches rápidos.
- No revelamos nombres de clientes (discreción y seguridad).

Si el usuario quiere agendar: Cal.com link, WhatsApp, o el correo codigobeta3.3@gmail.com.

Responde SIEMPRE en 1-3 oraciones, máximo 80 palabras. Sé directo. No repitas el saludo en cada respuesta.`;

    const history = [];
    let busy = false;

    const scrollDown = () => {
      requestAnimationFrame(() => { body.scrollTop = body.scrollHeight; });
    };

    const addMsg = (role, text, opts = {}) => {
      const el = document.createElement('div');
      el.className = 'ai-msg ai-msg--' + (role === 'user' ? 'user' : 'bot');
      if (opts.typing) el.classList.add('ai-msg--typing');
      const initials = role === 'user' ? 'TU' : 'CB';
      const p = document.createElement('p');
      p.textContent = text || '';
      const from = document.createElement('span');
      from.className = 'ai-msg__from';
      from.textContent = initials;
      el.appendChild(from);
      el.appendChild(p);
      // Insert before suggestions if they exist, otherwise append
      if (suggestions && suggestions.parentNode === body) {
        body.insertBefore(el, suggestions);
      } else {
        body.appendChild(el);
      }
      scrollDown();
      return { el, p };
    };

    const open = () => {
      panel.classList.add('is-open');
      panel.setAttribute('aria-hidden', 'false');
      fab.classList.add('is-hidden');
      setTimeout(() => input.focus(), 200);
    };
    const close = () => {
      panel.classList.remove('is-open');
      panel.setAttribute('aria-hidden', 'true');
      fab.classList.remove('is-hidden');
    };

    fab.addEventListener('click', open);
    closeBtn.addEventListener('click', close);
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && panel.classList.contains('is-open')) close();
    });

    const ask = async (text) => {
      if (busy || !text.trim()) return;
      busy = true;
      sendBtn.disabled = true;
      input.value = '';

      addMsg('user', text);
      history.push({ role: 'user', content: text });

      // Hide suggestions after first interaction
      if (suggestions) suggestions.style.display = 'none';

      const typing = addMsg('bot', '', { typing: true });

      try {
        const messages = [
          ...history,
        ];
        const reply = await window.claude.complete({
          system: SYSTEM,
          messages,
        });
        typing.el.classList.remove('ai-msg--typing');
        typing.p.textContent = reply || 'Disculpa, no pude responder. Intenta de nuevo o escríbenos directo.';
        history.push({ role: 'assistant', content: reply || '' });
      } catch (err) {
        typing.el.classList.remove('ai-msg--typing');
        typing.p.textContent = 'Hay un problema técnico. Escríbenos directo a codigobeta3.3@gmail.com o por WhatsApp.';
        console.warn('[ai] error', err);
      } finally {
        busy = false;
        sendBtn.disabled = false;
        scrollDown();
      }
    };

    form.addEventListener('submit', (e) => {
      e.preventDefault();
      ask(input.value);
    });

    if (suggestions) {
      suggestions.querySelectorAll('button[data-prompt]').forEach((b) => {
        b.addEventListener('click', () => ask(b.dataset.prompt));
      });
    }
  };

  return { boot };
})();

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', CodigoBeta.boot);
} else {
  CodigoBeta.boot();
}
