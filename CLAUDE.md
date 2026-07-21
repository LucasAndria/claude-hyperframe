# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

The video production workspace for **La Petite Crèche**. Every video is a self-contained
project folder under `projects/`, built and rendered with **HyperFrames** (HTML → video).

## Creating and working on videos — the HyperFrames skills own the flow

**Any request to make, edit, or render a video starts at the `/hyperframes` skill.** It
confirms the brief (intent layer), routes to the owning workflow (`/motion-graphics`,
`/general-video`, `/faceless-explainer`, …), and that workflow drives everything:
`hyperframes init` scaffold, `BRIEF.md`, composition authoring, `check`, preview,
approval gate, render. Do not re-invent this flow from repo docs — the skills are the
source of truth for how a video gets made.

**One repo-level override**: the skills default to `videos/<project-name>/`; here every
project lives in **`projects/<CODE>/`** instead. Scaffold with
`npx hyperframes init projects/<CODE> --non-interactive --example=blank` and keep
everything belonging to that video inside its folder. NEVER put per-video files at the
repo root, and NEVER touch another video's folder.

A typical skill-built project (see `projects/NEXT10S/` — a complete worked example):

```
projects/<CODE>/
├── BRIEF.md            confirmed intent (written by the workflow) — COMMITTED
├── CHECKLIST.md        living task list, ticked at every step — COMMITTED
├── hyperframes.json    project config (written by init) — COMMITTED
├── index.html          the composition — COMMITTED (+ fonts/, vendor/, compositions/)
├── shot-plan.json      workflow IR, when the workflow produces one — COMMITTED
├── snapshots/          proof frames / contact sheets              [gitignored]
├── renders/            rendered MP4s                              [gitignored]
└── final/              the delivered <CODE>.mp4                   [gitignored]
```

The final deliverable never sits next to intermediates: copy it to
`projects/<CODE>/final/<CODE>.mp4` and point the user there.

Useful commands (per project, from its folder): `npm run dev` (preview server — always
background), `npm run check`, `npx hyperframes render . -q high -o ./renders/video.mp4`,
`npx hyperframes doctor`. Media (SFX, music, images, icons, TTS, grades) resolves through
the `media-use` skill; HyperFrames compositions render without audio unless the
composition includes it — mux sound with ffmpeg afterwards when the piece needs it.

## Shared assets (`shared/`)

- `shared/fonts/Montserrat.ttf` — canonical brand font (variable, 100–900); copy into a
  project's `fonts/` and declare with a local `@font-face`.
- `shared/vendor/gsap.min.js` — local GSAP; copy into a project's `vendor/` (no CDN).
- `shared/brand.md` — palette (cream `#fbf6ef`, terracotta `#d98b63`, muted `#d8cabb`,
  ink `#271c16`), typography, and overlay-style rules for La Petite Crèche brand videos.
  Follow it when the video is for the brand; a non-brand piece may define its own palette
  in its BRIEF.
- `shared/motion/` — deterministic reference-explainer motion library
  (`reference-motion.js`, `window.RefMotion`) used by the legacy overlay pipeline.

## Legacy EMO avatar pipeline (scoped — only for `config.json` + `sequences.json` projects)

The EMO explainer videos (EMO03, EMO07, EMO14, …) were produced by an Excel-script avatar
pipeline: HeyGen avatar clips → AI b-roll → `python studio.py build` (ffmpeg assembly) →
HyperFrames overlay in `public/` → `python studio.py render`. Its rules live in
**`instruction.md`** and the French team guide **`GUIDE.md`**, and apply ONLY to projects
that carry `config.json` + `script.xlsx` + `sequences.json`. `python studio.py status`
shows the dashboard for those projects; `main.py` is a thin reference orchestrator.
Do NOT apply this pipeline — or `studio.py` — to HyperFrames-native projects, and do not
apply the HyperFrames workflow docs to a legacy resume: each flow is self-contained.

## Conventions & gotchas

- **ffmpeg limits here**: `drawtext`/`montage` are not available. To review clips,
  extract mid-frames and build a `tile` contact sheet; label by grid position. Keep QA
  frames in `review_frames/` or `snapshots/` inside the video folder (gitignored).
- **Gitignored per video**: `output/`, `source-video/`, `heygen_clips/`,
  `higgsfield/stills|clips/`, `segments/`, `renders/`, `review_frames/`, `ov_frames/`,
  `snapshots/`, `final/`, and all `*.mp4`/`*.mp3`. Committed sources = md/json/py/html/
  js/css + fonts + authored images. Installed skills are restored from `skills-lock.json`.
- ffmpeg and ffprobe must be on PATH. `hyperframes` runs via `npx` (no root package.json;
  each project pins its own CLI version in its `package.json`).
