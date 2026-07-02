# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A local, Claude-driven video pipeline for **La Petite Crèche** "EMO" emotional-parenting
explainer videos (EMO03, EMO07, EMO14, …). It turns a per-video Excel script into a finished
MP4 by chaining: **HeyGen** avatar talking-head clips → **Higgsfield** AI b-roll for non-avatar
scenes → **ffmpeg** assembly → **HyperFrames** HTML typographic overlays.

The heavy lifting runs through **MCP tools driven by Claude inside Claude Code**, not by a
plain `python main.py`. `main.py` is a thin reference orchestrator whose HeyGen step is still a
placeholder (`generate_heygen_video` raises "not implemented"); real production happens via the
MCP tools + per-video build scripts described below.

## One folder per video — the core rule

**Everything belonging to a video lives in `videos/<CODE>/`** (script, config, sequences,
generated clips, composition, output). NEVER put per-video files at the repo root, and NEVER
overwrite or delete another video's folder when starting a new one.

```
videos/<CODE>/
├── config.json            per-video settings (avatar, voice, fps, orientation) — COMMITTED
├── script.xlsx            validated Excel script — COMMITTED
├── sequences.json         structured source of truth — COMMITTED
├── build_base.py          per-video assembly script — COMMITTED
├── heygen_clips/          seqNN.mp4 (HeyGen MCP)                      [gitignored]
├── higgsfield/            stills/ + clips/ + *_ids.json               [media gitignored]
├── source-video/          (alt) pre-recorded base clip                [gitignored]
├── public/                HyperFrames overlay composition — COMMITTED (html/js/fonts)
└── output/                <CODE>_1_base.mp4, <CODE>_2_overlay.mp4, <CODE>.mp4  [gitignored]
```

Shared at the root: `motion/` (reusable motion library, staged into each video's
`public/vendor/`), `main.py`, `new_video.py`.

## Commands

```bash
# Scaffold a NEW video project (creates videos/<CODE>/ with config, dirs, motion staged)
python new_video.py <CODE> [--script path.xlsx] [--vertical]

# Assemble the edited base video for a video
python videos/<CODE>/build_base.py          # -> videos/<CODE>/output/<CODE>_1_base.mp4

# Render the HyperFrames overlay composition to a SILENT mp4 (mux audio back after)
npx hyperframes render videos/<CODE>/public --fps 25
npx hyperframes doctor            # troubleshoot the Node/Chrome render environment

# Reference orchestrator, per video (HeyGen step is a placeholder — see note above)
python main.py <CODE>

pip install openpyxl              # required to read .xlsx scripts
```

There are no tests, linters, or a package.json — `hyperframes` runs via `npx`.
ffmpeg and ffprobe must be on PATH.

## The proven per-video workflow (see `videos/EMO14_VID01/` — the template)

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
- **`build_base.py`** — assembles the edit: `emy` segments used as-is; `broll` segments take
  video from the b-roll trimmed to the HeyGen clip's exact duration + audio from the HeyGen clip
  (Emy VO). Everything normalised to **1920×1080 / 25fps / h264 yuv420p / aac 48k stereo**, then
  concatenated → `videos/<CODE>/output/<CODE>_1_base.mp4`.
- **HyperFrames overlays** — `public/index.html` is a `graphic-overlays` composition: base video
  full-bleed throughout, ~8 restrained typographic beats (Montserrat, warm cream/terracotta
  palette, gentle fades, scrims for legibility). Render silent, then ffmpeg-mux the base audio →
  `videos/<CODE>/output/<CODE>.mp4`.

## Motion library (`motion/`)

A reusable, deterministic **reference-explainer** motion library (`motion/reference-motion.js`,
exposes `window.RefMotion`; restrained push-ins, parallax, clean card/PIP reveals).
`main.py`'s `stage_motion_assets` (also called by `new_video.py`) copies it plus
`motion/motion.config.json`'s `motionStyle` into a composition's `public/vendor/`. Tune
intensity globally in `motion/motion.config.json` (`intensity`, default 0.65 — subtle).
Worked example in `motion/example/`.

## Conventions & gotchas

- **Excel script columns**: `Séq. | Durée | Texte validé | Type de sortie | Intention | Visuel
  recommandé | Prompt visuel`. `main.py`'s `_read_xlsx` flattens all cells naively; the real
  workflow instead reads structured data into `sequences.json`.
- **Per-video `config.json` is committed** (it holds project data: avatar/voice/fps/orientation,
  no secrets). If it's missing, `main.py` falls back to the Emy/Audrey defaults. Relative paths
  in it resolve against the video folder first, then the repo root (for shared `motion/`).
- **HeyGen + Higgsfield MCPs need OAuth (`/mcp`) and disconnect/reconnect often.** If a `mcp__*`
  tool is missing, reconnect before assuming a capability is unavailable.
- **HyperFrames render is always silent** — audio is muxed back with ffmpeg in a later step.
- **ffmpeg limits here**: `drawtext`/`montage` are not available. To review clips, extract
  mid-frames and build a `tile` contact sheet; label by grid position. Keep QA frames in
  `review_frames/` or `ov_frames/` inside the video folder (gitignored).
- **Recover the Montserrat font from git** if missing:
  `git show HEAD:videos/EMO03_VID01/public/vendor/fonts/Montserrat.ttf`.
- **Gitignored per video**: `output/`, `source-video/`, `heygen_clips/`, `higgsfield/stills|clips/`,
  `segments/`, `renders/`, `review_frames/`, `ov_frames/`, `snapshots/`, and all `*.mp4`/`*.mp3`.
  Committed video sources = xlsx/json/py/html/js/css + authored `public/assets` images.
  Installed skills are restored from `skills-lock.json`.
