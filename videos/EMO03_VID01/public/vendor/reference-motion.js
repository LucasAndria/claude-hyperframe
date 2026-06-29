/*
 * reference-motion.js — reference-explainer motion system for HyperFrames compositions.
 *
 * Polished AI/YouTube-explainer motion: restrained, editorial, deterministic.
 * Loads as a plain <script> in a HyperFrames composition (after gsap.min.js) and
 * exposes `window.RefMotion`. Also usable in Node (module.exports) for testing the
 * pure math layer.
 *
 * Two layers:
 *   - PURE (testable, no GSAP): easing, seededRange, interpolateTransform,
 *     getSceneMotionPreset, sampleCameraTransform, clampTransform.
 *   - APPLY (browser, needs window.gsap): applyCameraMotion, applyPipMotion,
 *     applyParallaxMotion, transitions.
 *
 * Determinism: NO Math.random() at render. All jitter is derived from a stable
 * scene `seed` via a seeded RNG. Same (seed, time) -> same transform, every render.
 */
(function (root, factory) {
  var api = factory();
  if (typeof module !== "undefined" && module.exports) module.exports = api; // Node
  if (root) root.RefMotion = api; // browser
})(typeof window !== "undefined" ? window : null, function () {
  "use strict";

  // ---------------------------------------------------------------------------
  // Global style (overridable via window.MOTION_STYLE, set by the composition)
  // ---------------------------------------------------------------------------
  var DEFAULT_STYLE = {
    name: "reference_explainer",
    intensity: 0.65, // 0 = no motion, 1 = full reference intensity (subtle by design)
    cameraMotion: "subtle", // "off" | "subtle" | "standard"
    transitionStyle: "editorial",
    allowRotation: false,
    pipStyle: "rounded_stable",
    screenRecordingMotion: "readable_slow",
  };

  function style() {
    var s = (typeof window !== "undefined" && window.MOTION_STYLE) || {};
    var out = {};
    for (var k in DEFAULT_STYLE) out[k] = DEFAULT_STYLE[k];
    for (var j in s) if (s[j] != null) out[j] = s[j];
    return out;
  }

  // intensity scalar applied to every motion *delta* (never to readability).
  function intensity() {
    var i = style().intensity;
    if (i == null) i = 0.65;
    if (style().cameraMotion === "off") return 0;
    return Math.max(0, Math.min(1.2, i));
  }

  // ---------------------------------------------------------------------------
  // Easing
  // ---------------------------------------------------------------------------
  function clamp01(t) { return t < 0 ? 0 : t > 1 ? 1 : t; }
  function easeOutCubic(t) { t = clamp01(t); var u = 1 - t; return 1 - u * u * u; }
  function easeInOutCubic(t) { t = clamp01(t); return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; }
  function smoothstep(t) { t = clamp01(t); return t * t * (3 - 2 * t); }
  function linear(t) { return clamp01(t); }

  var EASES = { easeOutCubic: easeOutCubic, easeInOutCubic: easeInOutCubic, smoothstep: smoothstep, linear: linear };
  // map our easing names -> GSAP ease strings (used by the APPLY layer)
  var GSAP_EASE = { easeOutCubic: "power2.out", easeInOutCubic: "power2.inOut", smoothstep: "power1.inOut", linear: "none" };

  // ---------------------------------------------------------------------------
  // Seeded randomness (planning/jitter only — deterministic)
  // ---------------------------------------------------------------------------
  function hashSeed(seed) {
    seed = String(seed == null ? "seed" : seed);
    var h = 2166136261 >>> 0;
    for (var i = 0; i < seed.length; i++) { h ^= seed.charCodeAt(i); h = Math.imul(h, 16777619); }
    return h >>> 0;
  }
  function mulberry32(a) {
    return function () {
      a |= 0; a = (a + 0x6d2b79f5) | 0;
      var t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  // deterministic value in [min,max] for a (seed,key) pair
  function seededRange(seed, min, max, key) {
    var r = mulberry32(hashSeed(String(seed) + "::" + (key || "")))();
    return min + (max - min) * r;
  }

  // ---------------------------------------------------------------------------
  // Transforms
  // ---------------------------------------------------------------------------
  function clampTransform(tf, role) {
    var out = { scale: tf.scale == null ? 1 : tf.scale, x: tf.x || 0, y: tf.y || 0, rotation: tf.rotation || 0, opacity: tf.opacity == null ? 1 : tf.opacity };
    // scale: natural range (section 11)
    out.scale = Math.max(1.0, Math.min(1.15, out.scale));
    // rotation: off unless explicitly allowed, role-capped
    var maxRot = 0;
    if (style().allowRotation) {
      if (role === "talkingHead") maxRot = 0.2;
      else if (role === "card" || role === "graphic") maxRot = 0.5;
      else maxRot = 0; // screen recording, pip
    }
    out.rotation = Math.max(-maxRot, Math.min(maxRot, out.rotation));
    out.opacity = clamp01(out.opacity);
    return out;
  }

  // linear interpolation between two transform objects with an eased t
  function interpolateTransform(from, to, t, ease) {
    var fn = typeof ease === "function" ? ease : EASES[ease] || easeInOutCubic;
    var e = fn(t);
    var keys = {}, k;
    for (k in from) keys[k] = 1;
    for (k in to) keys[k] = 1;
    var out = {};
    for (k in keys) {
      var a = from[k] == null ? (k === "scale" || k === "opacity" ? 1 : 0) : from[k];
      var b = to[k] == null ? (k === "scale" || k === "opacity" ? 1 : 0) : to[k];
      out[k] = a + (b - a) * e;
    }
    return out;
  }

  // ---------------------------------------------------------------------------
  // Preset specs — data, scaled by global intensity. Ranges follow the brief.
  // ---------------------------------------------------------------------------
  function scaleDelta(from, to, k) { return from + (to - from) * k; }

  function getSceneMotionPreset(name, seed) {
    var k = intensity();
    seed = seed == null ? name : seed;
    switch (name) {
      case "talkingHeadWide":
        return { role: "talkingHead", kind: "pushIn",
          scaleFrom: 1.0, scaleTo: scaleDelta(1.0, 1.03, k), ease: "easeInOutCubic",
          driftX: seededRange(seed, 0, 8, "dx") * k, driftY: seededRange(seed, 0, 6, "dy") * k };
      case "talkingHeadMedium":
        return { role: "talkingHead", kind: "pushIn",
          scaleFrom: 1.06, scaleTo: scaleDelta(1.06, 1.10, k), ease: "easeInOutCubic",
          driftX: seededRange(seed, -10, 10, "dx") * k, driftY: seededRange(seed, -6, 8, "dy") * k };
      case "talkingHeadPunchIn":
        var cut = 1.10 + (seededRange(seed, 0, 0.04, "cut")); // 1.10–1.14 (editorial, not scaled down to nothing)
        return { role: "talkingHead", kind: "punchIn",
          cutTo: cut, slowTo: cut + 0.01 + 0.01 * k, ease: "easeInOutCubic" };
      case "darkExplainer":
        return { role: "graphic", kind: "ambientDrift",
          driftX: seededRange(seed, 5, 15, "bgx") * k, driftY: seededRange(seed, 4, 12, "bgy") * k, ease: "linear" };
      case "floatingCard":
        return { role: "card", kind: "reveal",
          fromY: 20, fromScale: 0.98, fromOpacity: 0, ease: "easeOutCubic",
          revealMs: 420, idleY: 3 * k, idleOpacity: 0.03 * k };
      case "pipPresenter":
        return { role: "pip", kind: "pipEnter",
          fromY: 12, fromScale: 0.96, fromOpacity: 0, ease: "easeOutCubic", enterFrames: 10 };
      case "screenRecording":
        return { role: "screen", kind: "slowPush",
          scaleFrom: 1.0, scaleTo: scaleDelta(1.0, 1.015, k), ease: "easeInOutCubic",
          panX: seededRange(seed, -24, 24, "px") * k, panY: seededRange(seed, -16, 16, "py") * k };
      case "screenFocus":
        return { role: "screen", kind: "focusZoom",
          scaleTo: scaleDelta(1.0, 1.08, k), ease: "easeInOutCubic", durationMs: 800 };
      case "staticHold":
      default:
        return { role: "static", kind: "hold" };
    }
  }

  // Pure sampler: transform of a camera preset at normalized scene time tNorm [0,1].
  // (Used by tests and any non-GSAP consumer.)
  function sampleCameraTransform(name, tNorm, seed) {
    var p = getSceneMotionPreset(name, seed);
    var t = clamp01(tNorm);
    var tf = { scale: 1, x: 0, y: 0, rotation: 0, opacity: 1 };
    if (p.kind === "pushIn" || p.kind === "slowPush") {
      tf = interpolateTransform(
        { scale: p.scaleFrom, x: 0, y: 0 },
        { scale: p.scaleTo, x: p.driftX || p.panX || 0, y: p.driftY || p.panY || 0 },
        t, p.ease);
    } else if (p.kind === "punchIn") {
      // instant cut at t=0, then a very slow push
      tf.scale = p.cutTo + (p.slowTo - p.cutTo) * easeInOutCubic(t);
    } else if (p.kind === "ambientDrift") {
      tf = interpolateTransform({ x: 0, y: 0 }, { x: p.driftX, y: p.driftY }, t, "linear");
      tf.scale = 1;
    } else if (p.kind === "focusZoom") {
      tf.scale = 1 + (p.scaleTo - 1) * easeInOutCubic(t);
    }
    return clampTransform(tf, p.role);
  }

  // ---------------------------------------------------------------------------
  // APPLY layer (needs window.gsap). Each adds tweens to a paused timeline `tl`.
  // ---------------------------------------------------------------------------
  function requireGsap() {
    if (typeof window === "undefined" || !window.gsap)
      throw new Error("RefMotion apply* needs window.gsap (load gsap.min.js first).");
    return window.gsap;
  }
  function f2s(frames, fps) { return frames / (fps || 30); }

  // Camera motion on a wrapper element (e.g. #video-wrap or a scene wrapper).
  // opts: { startSec, sceneDuration, fps, seed, focusPoint:{xPct,yPct}, canvas:{w,h} }
  function applyCameraMotion(tl, target, name, opts) {
    requireGsap();
    opts = opts || {};
    var start = opts.startSec || 0;
    var dur = Math.max(0.1, opts.sceneDuration || 6);
    var p = getSceneMotionPreset(name, opts.seed != null ? opts.seed : name);
    tl.set(target, { transformOrigin: "50% 50%" }, start);

    if (p.kind === "pushIn") {
      tl.fromTo(target, { scale: p.scaleFrom, x: 0, y: 0 },
        { scale: p.scaleTo, x: p.driftX, y: p.driftY, duration: dur, ease: GSAP_EASE[p.ease] }, start);
    } else if (p.kind === "punchIn") {
      tl.set(target, { scale: p.cutTo }, start); // editorial cut — instant, not animated
      tl.to(target, { scale: p.slowTo, duration: dur, ease: GSAP_EASE[p.ease] }, start);
    } else if (p.kind === "slowPush") {
      var cap = Math.min(dur, 20);
      tl.fromTo(target, { scale: p.scaleFrom, x: 0, y: 0 },
        { scale: p.scaleTo, x: p.panX, y: p.panY, duration: cap, ease: GSAP_EASE[p.ease] }, start);
    } else if (p.kind === "focusZoom") {
      var fp = opts.focusPoint || { xPct: 50, yPct: 50 };
      var cw = (opts.canvas && opts.canvas.w) || 1280, ch = (opts.canvas && opts.canvas.h) || 720;
      // pan so the focus point moves toward center, bounded
      var px = clampNum(((50 - fp.xPct) / 100) * cw * (p.scaleTo - 1), -0.18 * cw, 0.18 * cw);
      var py = clampNum(((50 - fp.yPct) / 100) * ch * (p.scaleTo - 1), -0.18 * ch, 0.18 * ch);
      var ms = (p.durationMs || 800) / 1000;
      tl.to(target, { scale: p.scaleTo, x: px, y: py, duration: ms, ease: GSAP_EASE[p.ease] }, start);
    }
    return tl;
  }
  function clampNum(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }

  // PIP entrance, then anchored (no floating). opts: { startSec, fps }
  function applyPipMotion(tl, target, opts) {
    requireGsap();
    opts = opts || {};
    var start = opts.startSec || 0;
    var p = getSceneMotionPreset("pipPresenter");
    tl.set(target, { transformOrigin: "50% 100%" }, start);
    tl.fromTo(target,
      { autoAlpha: p.fromOpacity, scale: p.fromScale, y: p.fromY },
      { autoAlpha: 1, scale: 1, y: 0, duration: f2s(p.enterFrames, opts.fps), ease: GSAP_EASE[p.ease] }, start);
    // intentionally nothing after — PIP stays put.
    return tl;
  }

  // Parallax drift for graphic scenes. layers: [{ el, depth }] depth 0(bg)..1(fg).
  // Foreground drifts a little faster than background; all slow + linear.
  function applyParallaxMotion(tl, layers, opts) {
    requireGsap();
    opts = opts || {};
    var start = opts.startSec || 0;
    var dur = Math.max(0.1, opts.sceneDuration || 6);
    var k = intensity();
    var base = 12 * k; // px at depth 0.5
    (layers || []).forEach(function (layer, i) {
      var depth = layer.depth == null ? 0.4 : layer.depth;
      var mag = base * (0.4 + depth); // bg slower, fg faster
      var ang = seededRange(opts.seed != null ? opts.seed : "px", 0, Math.PI * 2, "ang" + i);
      var dx = clampNum(Math.cos(ang) * mag, -20, 20);
      var dy = clampNum(Math.sin(ang) * mag, -20, 20);
      tl.fromTo(layer.el, { x: 0, y: 0 }, { x: dx, y: dy, duration: dur, ease: "none" }, start);
    });
    return tl;
  }

  // Card/text reveal (floatingCard). opts: { startSec, fps }
  function applyCardReveal(tl, target, opts) {
    requireGsap();
    opts = opts || {};
    var start = opts.startSec || 0;
    var p = getSceneMotionPreset("floatingCard");
    tl.fromTo(target,
      { autoAlpha: p.fromOpacity, y: p.fromY, scale: p.fromScale },
      { autoAlpha: 1, y: 0, scale: 1, duration: (p.revealMs) / 1000, ease: GSAP_EASE[p.ease] }, start);
    return tl;
  }

  // Editorial transitions. `blackEl` is a full-frame black overlay div the caller provides.
  var transitions = {
    hardCut: function () { /* default — nothing to animate */ },
    fadeThroughBlack: function (tl, blackEl, atSec, frames, fps) {
      requireGsap();
      var d = f2s((frames || 8) / 2, fps);
      tl.to(blackEl, { autoAlpha: 1, duration: d, ease: "none" }, atSec);
      tl.to(blackEl, { autoAlpha: 0, duration: d, ease: "none" }, atSec + d);
    },
    crossfade: function (tl, fromEl, toEl, atSec, frames, fps) {
      requireGsap();
      var d = f2s(frames || 10, fps);
      tl.to(fromEl, { autoAlpha: 0, duration: d, ease: "none" }, atSec);
      tl.fromTo(toEl, { autoAlpha: 0 }, { autoAlpha: 1, duration: d, ease: "none" }, atSec);
    },
  };

  return {
    // style
    DEFAULT_STYLE: DEFAULT_STYLE, style: style, intensity: intensity,
    // easing
    easeOutCubic: easeOutCubic, easeInOutCubic: easeInOutCubic, smoothstep: smoothstep, linear: linear, EASES: EASES,
    // rng + transforms
    seededRange: seededRange, clampTransform: clampTransform, interpolateTransform: interpolateTransform,
    // presets
    getSceneMotionPreset: getSceneMotionPreset, sampleCameraTransform: sampleCameraTransform,
    // apply (browser)
    applyCameraMotion: applyCameraMotion, applyPipMotion: applyPipMotion,
    applyParallaxMotion: applyParallaxMotion, applyCardReveal: applyCardReveal,
    transitions: transitions,
  };
});
