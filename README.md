# Avatar Video Pipeline

Minimal local automation: takes a base video — either generated from a script
with a HeyGen avatar **or** a clip you drop in `source-video/` — enhances it with
Hyperframe, and runs ffmpeg to produce a final MP4 saved locally.

## Flow

```
            ┌─ source: "avatar" ─ scripts/script.{txt,md,csv,xlsx} -> HeyGen avatar ─┐
base video ─┤                                                                        ├─> Hyperframe motion -> ffmpeg (MP4) -> output/<name>.mp4
            └─ source: "video"  ─ source-video/<clip>.mp4 ──────────────────────────┘
```

## Video source: avatar or your own clip

Set `"source"` in `config.json`:

- `"avatar"` — generate the base video from `script_file` with a HeyGen avatar
  (`avatar_id` / optional `voice_id`).
- `"video"` — skip HeyGen and use a pre-recorded file. Drop it in `source-video/`
  and point `source_video.file` at it. The clip keeps its own audio.

## Setup

1. Install [Python 3.9+](https://www.python.org/) and [ffmpeg](https://ffmpeg.org/download.html) (must be on PATH).
2. Copy the config and fill in your values:
   ```bash
   cp config.example.json config.json
   ```
   Set `source` to `"avatar"` or `"video"` (see above).
   For `"avatar"`: set `heygen.avatar_id`; leave `heygen.voice_id` empty (`""`) to
   use the avatar's default voice, or set a specific voice id to override it.
   For `"video"`: set `source_video.file` to your clip in `source-video/`.
   Set `orientation` to `"vertical"` (9:16, for Reels/TikTok/Shorts) or
   `"horizontal"` (16:9, for YouTube/desktop).
3. (Avatar source only) Put your script file in the `scripts/` folder (or set
   `script_file` in `config.json`). Supported formats: `.txt`, `.md`, `.csv`, `.xlsx`.
   For `.xlsx` also install openpyxl: `pip install openpyxl`.

## How to trigger generation

The HeyGen step runs through the **HeyGen MCP**, which is driven by Claude — so
generation is triggered inside Claude Code, not by a plain `python` run alone.

1. Open this folder in **Claude Code**.
2. Put your script in `scripts/` and set `avatar_id` in `config.json`.
3. Ask Claude, e.g.:
   > Generate the video from `scripts/script.txt`.

   Claude reads the script, calls the HeyGen MCP (`create_video_from_avatar`)
   with your avatar/voice, enhances with Hyperframe, runs ffmpeg, and saves the
   final MP4 to `output/`.

Once the two MCP/CLI steps in `main.py` are wired up, you can also run the whole
pipeline directly:

```bash
python main.py
```

Either way, the final video is written to `output/<script-name>.mp4` (named after
your script file, e.g. `script.txt` → `output/script.mp4`). Intermediate files
(`<name>_1_heygen.mp4`, `<name>_2_hyperframe.mp4`) are also kept in `output/`.

## Implement the integrations

Two steps ship as clear placeholders marked with `TODO` in `main.py`:

- **`generate_heygen_video`** — call the HeyGen **MCP** tool
  (`create_video_from_avatar`) and download the result. Auth is handled by the
  MCP, so no API key is stored in config.
- **`enhance_with_hyperframe`** — **implemented**: renders a Hyperframes overlay
  composition (`videos/<name>/public/index.html`) to video via `npx hyperframes render`.
  The composition (timed keyword/typography cards over the avatar) is authored once
  with the `graphic-overlays` skill; if none exists, the avatar video passes through.

The **ffmpeg** step is fully implemented: converts to clean H.264/AAC MP4 and muxes
the narration audio back in (the Hyperframes render is silent).

## Motion system

A reusable, deterministic **reference-explainer** motion library lives in `motion/`
(restrained push-ins, parallax, clean card/PIP reveals, editorial cuts). `main.py`
auto-stages it into every composition, so any HyperFrames scene can use
`window.RefMotion` presets. Tune intensity globally in `motion/motion.config.json`
(`motionStyle.intensity`, default 0.65 — subtle). See `motion/README.md` for presets,
recipes, and the worked example in `motion/example/`.

## Output files

For a base named `<name>` (the script stem for the avatar source, or the clip
stem for the video source), `output/` gets:
- `<name>_1_heygen.mp4` — raw HeyGen avatar (avatar source only)
- `<name>_2_hyperframe.mp4` — silent Hyperframes overlay render
- `<name>.mp4` — **final**: base video + timed typography overlays + audio

Authored overlay compositions live in `videos/<name>/public/index.html` (created
with the `graphic-overlays` skill); if none exists, the base video passes through.

## Error handling

The pipeline logs and exits with a clear message for: missing config, missing or
empty script, failed HeyGen generation, failed Hyperframe processing, missing
ffmpeg, and ffmpeg errors.
