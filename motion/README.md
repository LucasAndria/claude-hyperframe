# Reference-explainer motion system

A reusable, **deterministic** motion library for the HyperFrames render stage that
reproduces a polished AI/YouTube-explainer feel: restrained push-ins, slow parallax,
clean card/PIP reveals, editorial hard cuts. Motion supports narration — it never
competes with it.

## Files

| File | Purpose |
|---|---|
| `reference-motion.js` | The library — exposes `window.RefMotion` (browser) and `module.exports` (Node). |
| `motion.config.json` | **The global config.** The one place to tune intensity/behaviour. |
| `example/public/index.html` | Worked example — Recipe B (dark explainer + PIP), 16:9 1280×720. |
| `selftest.mjs` | `node motion/selftest.mjs` — verifies determinism, clamps, easing. |

## How it works

The library has two layers:

- **Pure (deterministic, testable, no GSAP):** `easeOutCubic`, `easeInOutCubic`,
  `smoothstep`, `linear`, `seededRange`, `interpolateTransform`, `clampTransform`,
  `getSceneMotionPreset`, `sampleCameraTransform`.
- **Apply (browser, needs `window.gsap`):** `applyCameraMotion`, `applyPipMotion`,
  `applyParallaxMotion`, `applyCardReveal`, `transitions.{hardCut,fadeThroughBlack,crossfade}`.

**Determinism:** no `Math.random()` at render. All jitter comes from `seededRange(seed,…)`
using a stable per-scene seed, so the same `(seed, time)` always yields the same transform.

### Presets

| Preset | Motion |
|---|---|
| `talkingHeadWide` | micro push-in 1.00→1.03 over the scene, ±a few px drift |
| `talkingHeadMedium` | push-in 1.06→1.10, slightly more drift |
| `talkingHeadPunchIn` | **instant cut** to 1.10–1.14 (not animated), then a very slow push |
| `darkExplainer` | slow background ambient drift (5–15 px) |
| `floatingCard` | reveal: opacity 0→1, y 20→0, scale .98→1, easeOutCubic; near-static after |
| `pipPresenter` | entrance opacity 0→1, scale .96→1, y 12→0 (≈10 frames), then anchored |
| `screenRecording` | slow push 1.00→1.015 + ≤24 px pan over the scene |
| `screenFocus` | focus zoom to ≤1.08, pan toward a focus point, ~800 ms |
| `staticHold` | nothing |

### Natural-motion clamps (always enforced)

- scale ∈ **[1.00, 1.15]**
- rotation **0** unless `allowRotation` (then talking-head ±0.2°, cards ±0.5°, screen 0°)
- talking-head translation small; card idle drift ±2–4 px; background drift ≤20 px

## Tuning globally

Edit **`motion.config.json`**:

```json
{ "motionStyle": {
    "name": "reference_explainer",
    "intensity": 0.65,            // 0 = none … 1 = full reference (subtle by design)
    "cameraMotion": "subtle",     // "off" | "subtle" | "standard"
    "transitionStyle": "editorial",
    "allowRotation": false,
    "pipStyle": "rounded_stable",
    "screenRecordingMotion": "readable_slow"
} }
```

`intensity` scales every motion **delta** (not readability). `cameraMotion: "off"`
freezes camera motion entirely. Lower intensity → more restrained; the default 0.65
is intentionally subtle. The pipeline injects this into each composition as
`window.MOTION_STYLE` (via `vendor/motion-style.js`), and the library merges it over
its built-in defaults.

## Applying it to a generated video

`main.py` calls `stage_motion_assets()` before every render, copying
`reference-motion.js` + writing `motion-style.js` into the composition's
`public/vendor/`. So in any HyperFrames composition (e.g. authored by the
`graphic-overlays` skill), just load and use it:

```html
<script src="vendor/gsap.min.js"></script>
<script src="vendor/motion-style.js"></script>
<script src="vendor/reference-motion.js"></script>
<script>
  const RM = window.RefMotion;
  const tl = window.gsap.timeline({ paused: true });
  const ctx = { startSec: 0, sceneDuration: 8, fps: 30, seed: "scene-1", canvas: { w: 1280, h: 720 } };

  RM.applyCameraMotion(tl, "#video-wrap", "talkingHeadWide", ctx);   // Recipe A
  RM.applyCardReveal(tl, "#headline", { startSec: 0.3, fps: 30 });   // Recipe B / D
  RM.applyPipMotion(tl, "#pip", { startSec: 0.55, fps: 30 });        // Recipe B / C
  window.__timelines = (window.__timelines || {});
  window.__timelines["my-comp"] = tl;
</script>
```

### Scene recipes

- **A — full-screen talking head:** `applyCameraMotion(tl, target, "talkingHeadWide"|"talkingHeadMedium", ctx)`; punch-ins on idea changes via `"talkingHeadPunchIn"` at a new scene start.
- **B — dark explainer + PIP:** parallax bg + `applyCardReveal` (stagger 120–220 ms) + `applyPipMotion`. See `example/`.
- **C — screen recording + PIP:** `applyCameraMotion(tl, "#screen", "screenRecording", ctx)`; emphasis via `"screenFocus"` with `ctx.focusPoint = { xPct, yPct }`; PIP bottom-left/right.
- **D — UI/card montage:** sequential `applyCardReveal` with staggered `startSec`.

Verify any composition with `npx hyperframes lint <public-dir>` and preview a frame
with `npx hyperframes snapshot <public-dir> --at <sec>`.
