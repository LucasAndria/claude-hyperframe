# Avatar Video Pipeline

Local automation for **La Petite Crèche** EMO videos: each video is a fully
self-contained project folder under `projects/<CODE>/` (script, config, generated
clips, overlay composition, and output all live together). The pipeline turns a
per-video Excel script into a finished MP4: HeyGen avatar clips → Higgsfield
b-roll → ffmpeg assembly → HyperFrames typographic overlays.

## Layout: one folder per video

```
projects/<CODE>/                  e.g. projects/EMO14_VID01/
├── config.json                 per-video settings (avatar, voice, fps, orientation)
├── script.xlsx                 the validated Excel script
├── sequences.json              structured source of truth (roles, script per sequence)
├── build_base.py               assembles the edited base video (per-video)
├── heygen_clips/               seqNN.mp4 talking-head clips (HeyGen MCP)      [gitignored]
├── higgsfield/stills|clips/    b-roll stills + animated clips (Higgsfield)    [gitignored]
├── source-video/               (alt) drop a pre-recorded base clip here       [gitignored]
├── public/                     HyperFrames overlay composition (index.html)
└── output/                     ALL rendered results for this video            [gitignored]
    ├── <CODE>_1_base.mp4       assembled base edit
    ├── <CODE>_2_overlay.mp4    silent HyperFrames render
    └── <CODE>.mp4              final video
```

Shared, reusable pieces stay at the repo root:

- `motion/` — the deterministic reference-explainer motion library
  (`window.RefMotion`); it is auto-staged into each video's `public/vendor/`.
- `main.py` — the reference orchestrator (run per video, see below).
- `new_video.py` — scaffolds a new video folder.

Starting a new video **never touches another video's files** — no more
overwriting `scripts/`, `config.json`, or `output/` between videos.

## Start a new video

```bash
python new_video.py EMO15_VID01
# optionally: --script "path/to/EMO15_VID01.xlsx"   --vertical (9:16)
```

This creates `projects/EMO15_VID01/` with a default `config.json` (Emy avatar +
French voice Audrey, 16:9, 25 fps), a `sequences.json` stub, the standard
subfolders, and the motion library staged into `public/vendor/`.

Then, in Claude Code, ask e.g.:

> Build EMO15_VID01 from projects/EMO15_VID01/script.xlsx.

Claude fills `sequences.json`, generates the HeyGen clips and Higgsfield b-roll
via MCP, assembles the base with `build_base.py`, authors the HyperFrames
overlays in `public/`, and renders the final MP4 into `projects/EMO15_VID01/output/`.

## Run the reference orchestrator

```bash
python main.py EMO14_VID01        # or: python main.py projects/EMO14_VID01
```

- Reads `projects/<CODE>/config.json` (missing file = sensible defaults).
- `"source": "avatar"` — generate the base from `script.xlsx` with a HeyGen
  avatar (the HeyGen step is still a placeholder; real generation runs through
  the HeyGen MCP driven by Claude).
- `"source": "video"` — skip HeyGen and use a clip from the video's own
  `source-video/` folder.
- Renders the HyperFrames composition in `public/` (silent), then muxes the
  narration audio back with ffmpeg. Everything lands in `projects/<CODE>/output/`.

## Setup

1. Install [Python 3.10+](https://www.python.org/), [Node.js](https://nodejs.org/),
   and [ffmpeg](https://ffmpeg.org/download.html) (ffmpeg/ffprobe on PATH).
2. `pip install openpyxl` (to read `.xlsx` scripts).
3. HeyGen + Higgsfield run as MCP servers inside Claude Code (`/mcp` to
   authenticate) — no API keys stored in this repo.

## Motion system

A reusable, deterministic **reference-explainer** motion library lives in `motion/`
(restrained push-ins, parallax, clean card/PIP reveals, editorial cuts). It is
auto-staged into every composition's `public/vendor/`, so any HyperFrames scene
can use `window.RefMotion` presets. Tune intensity globally in
`motion/motion.config.json` (`motionStyle.intensity`, default 0.65 — subtle).
See `motion/README.md` and the worked example in `motion/example/`.

## Error handling

The pipeline logs and exits with a clear message for: unknown video folder,
missing or empty script, failed HeyGen generation, failed Hyperframe render,
missing ffmpeg, and ffmpeg errors.
