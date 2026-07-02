# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A local, Claude-driven video pipeline for **La Petite Crèche** "EMO" emotional-parenting
explainer videos (EMO03, EMO07, EMO14, …). It turns a per-video Excel script into a finished
MP4 by chaining: **HeyGen** avatar talking-head clips → **Higgsfield** AI b-roll for non-avatar
scenes → **ffmpeg** assembly → **HyperFrames** HTML typographic overlays.

The heavy lifting runs through **MCP tools driven by Claude inside Claude Code**; the
mechanical steps run through **`video.py`**, the single CLI. `main.py` is a thin reference
orchestrator whose HeyGen step is still a placeholder. `GUIDE.md` is the French step-by-step
guide for the team — keep it in sync when the workflow changes.

## One folder per video — the core rule

**Everything belonging to a video lives in `projects/<CODE>/`** (script, config, sequences,
generated clips, composition, output). NEVER put per-video files at the repo root, and NEVER
overwrite or delete another video's folder when starting a new one.

```
projects/<CODE>/
├── config.json            per-video settings (avatar, voice, fps, orientation) — COMMITTED
├── script.xlsx            validated Excel script — COMMITTED
├── sequences.json         structured source of truth — COMMITTED
├── heygen_clips/          seqNN.mp4 (HeyGen MCP)                      [gitignored]
├── higgsfield/            stills/ + clips/ + *_ids.json               [media gitignored]
├── source-video/          (alt) pre-recorded base clip                [gitignored]
├── public/                HyperFrames overlay composition — COMMITTED (html/js/fonts)
└── output/                <CODE>_1_base.mp4, <CODE>_2_overlay.mp4, <CODE>.mp4  [gitignored]
```

Shared at the root: `shared/` (motion library, Montserrat, GSAP, `brand.md` — auto-staged
into new projects), `video.py`, `main.py`, `GUIDE.md`.

## Commands — `video.py` is the single entry point

```bash
python video.py status              # dashboard: every project + its next step
python video.py new <CODE> [--script path.xlsx] [--vertical]   # scaffold a project
python video.py build <CODE>       # assemble base edit -> projects/<CODE>/output/<CODE>_1_base.mp4
python video.py render <CODE>      # render overlays (silent) + mux base audio -> final <CODE>.mp4

npx hyperframes doctor            # troubleshoot the Node/Chrome render environment
python main.py <CODE>            # reference orchestrator (HeyGen step is a placeholder)
pip install openpyxl              # required to read .xlsx scripts
```

There are no tests, linters, or a package.json — `hyperframes` runs via `npx`.
ffmpeg and ffprobe must be on PATH. Run `python video.py status` first to see where a
project stands before doing anything.

## The proven per-video workflow (see `projects/EMO14_VID01/` — the template)

- `sequences.json` — the source of truth: title, avatar_id, voice_id, fps, and an array of
  numbered sequences. Each sequence has `role: "emy"` (on-camera avatar talking head) or
  `role: "broll"` (Higgsfield b-roll with Emy's VO kept over it), plus script/intention/visual.
- **HeyGen** (`create_video_from_avatar`, one call per sequence) → `heygen_clips/seqNN.mp4`.
  Avatar **Emy** (`75255783465d403696e639a249a0b9c0`), French female voice **Audrey**
  (`7459d7aa599b4f97908600896a0e7ef4`). 16:9, 1080p, no captions. Inclusive endings voiced
  feminine ("épuisée") since the voice is female.
- **Higgsfield** for `broll` rows → build ONE reference-family still (nano_banana_2), save it as
  a reusable **Element**, generate per-beat stills referencing that element, animate each with
  Seedance 2.0 image-to-video (`generate_audio:false`) → `higgsfield/clips/brollNN.mp4`.
- **`video.py build`** — assembles the edit: `emy` segments used as-is; `broll` segments take
  video from the b-roll trimmed to the HeyGen clip's exact duration + audio from the HeyGen clip
  (Emy VO). Everything normalised (1920×1080 or 1080×1920 if vertical / fps from config / h264
  yuv420p / aac 48k stereo), then concatenated → `output/<CODE>_1_base.mp4`.
- **HyperFrames overlays** — `public/index.html` is a `graphic-overlays` composition: base video
  full-bleed throughout (as `public/input-video.mp4`), ~8 restrained typographic beats following
  `shared/brand.md` (Montserrat, cream/terracotta palette, gentle fades, scrims for legibility).
- **`video.py render`** — refreshes `public/input-video.mp4` from the base, renders the
  composition silent, then ffmpeg-muxes the base audio → `output/<CODE>.mp4`.

## Shared assets (`shared/`)

- `shared/motion/` — reusable, deterministic **reference-explainer** motion library
  (`reference-motion.js`, exposes `window.RefMotion`; restrained push-ins, parallax, clean
  card/PIP reveals). Staged into each composition's `public/vendor/` by `video.py new`, `video.py
  render`, and `main.py`. Tune intensity globally in `shared/motion/motion.config.json`
  (`intensity`, default 0.65 — subtle). Worked example in `shared/motion/example/`.
- `shared/fonts/Montserrat.ttf`, `shared/vendor/gsap.min.js` — copied into each new project's
  `public/` by `video.py new`.
- `shared/brand.md` — palette (cream `#fbf6ef`, terracotta `#d98b63`, muted `#d8cabb`, ink
  `#271c16`), typography, and overlay-style rules. Follow it in every composition.

## Conventions & gotchas

- **Excel script columns**: `Séq. | Durée | Texte validé | Type de sortie | Intention | Visuel
  recommandé | Prompt visuel`. The real workflow reads structured data into `sequences.json`.
- **Per-video `config.json` is committed** (avatar/voice/fps/orientation, no secrets). If it's
  missing, tools fall back to the Emy/Audrey defaults. Relative paths in it resolve against the
  video folder first, then the repo root (for `shared/`).
- **HeyGen + Higgsfield MCPs need OAuth (`/mcp`) and disconnect/reconnect often.** If a `mcp__*`
  tool is missing, reconnect before assuming a capability is unavailable.
- **HyperFrames render is always silent** — `video.py render` muxes the audio back automatically.
- **ffmpeg limits here**: `drawtext`/`montage` are not available. To review clips, extract
  mid-frames and build a `tile` contact sheet; label by grid position. Keep QA frames in
  `review_frames/` or `ov_frames/` inside the video folder (gitignored).
- **Recover the Montserrat font**: canonical copy at `shared/fonts/Montserrat.ttf`.
- **Gitignored per video**: `output/`, `source-video/`, `heygen_clips/`, `higgsfield/stills|clips/`,
  `segments/`, `renders/`, `review_frames/`, `ov_frames/`, `snapshots/`, and all `*.mp4`/`*.mp3`.
  Committed video sources = xlsx/json/py/html/js/css + authored `public/assets` images.
  Installed skills are restored from `skills-lock.json`.
