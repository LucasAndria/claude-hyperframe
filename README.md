# Avatar Video Pipeline

Local automation for **La Petite Crèche** EMO videos: each video is a fully
self-contained project folder under `projects/<CODE>/`, driven by **one
command** — `python emo.py`. The pipeline turns a per-video Excel script into a
finished MP4: HeyGen avatar clips → Higgsfield b-roll → ffmpeg assembly →
HyperFrames typographic overlays.

**Non-technical team members: read [GUIDE.md](GUIDE.md) (French, step by step).**

## The one command

```bash
python emo.py status                  # every project + its next step
python emo.py new EMO15_VID01        # scaffold a new self-contained project
python emo.py build EMO15_VID01      # assemble the base edit from the clips
python emo.py render EMO15_VID01     # render overlays + mux audio -> final MP4
```

`status` example:

```
PROJET         script seq     heygen  broll  base  overlays final  PROCHAINE ETAPE
EMO14_VID01    OK     19      19/19   10/10  OK    OK       OK     TERMINE
EMO14_VID02    OK     --      --      --     --    --       --     remplir sequences.json
```

## Layout: one folder per video

```
projects/<CODE>/                e.g. projects/EMO14_VID01/
├── config.json                 per-video settings (avatar, voice, fps, orientation)
├── script.xlsx                 the validated Excel script
├── sequences.json              structured source of truth (roles, script per sequence)
├── heygen_clips/               seqNN.mp4 talking-head clips (HeyGen MCP)      [gitignored]
├── higgsfield/stills|clips/    b-roll stills + animated clips (Higgsfield)    [gitignored]
├── source-video/               (alt) drop a pre-recorded base clip here       [gitignored]
├── public/                     HyperFrames overlay composition (index.html)
└── output/                     ALL rendered results for this video            [gitignored]
    ├── <CODE>_1_base.mp4       assembled base edit        (emo.py build)
    ├── <CODE>_2_overlay.mp4    silent HyperFrames render  (emo.py render)
    └── <CODE>.mp4              final video                (emo.py render)
```

Shared, reusable pieces live in `shared/` — staged automatically into every new
project by `emo.py new`:

- `shared/motion/` — deterministic reference-explainer motion library (`window.RefMotion`)
- `shared/fonts/Montserrat.ttf` + `shared/vendor/gsap.min.js` — brand font & animation lib
- `shared/brand.md` — the palette / typography / overlay-style reference

Starting a new video **never touches another video's files**.

## Production workflow

1. `python emo.py new <CODE> --script <file.xlsx>` — scaffold the project.
2. In Claude Code: *"Remplis sequences.json pour `<CODE>`"* — Claude structures
   the Excel script into sequences (Emy on-camera vs. b-roll).
3. *"Génère les clips HeyGen pour `<CODE>`"* — one clip per sequence via the
   HeyGen MCP (avatar Emy, French voice Audrey).
4. *"Génère les b-roll Higgsfield pour `<CODE>`"* — consistent visual family,
   animated with Seedance image-to-video.
5. `python emo.py build <CODE>` — ffmpeg assembles the edit (b-roll video +
   Emy VO, everything normalised and concatenated).
6. *"Crée les overlays HyperFrames pour `<CODE>`"* — Claude authors the
   typographic overlay composition in `public/`.
7. `python emo.py render <CODE>` — renders the overlays (silent) and muxes the
   base audio back in → `projects/<CODE>/output/<CODE>.mp4`.

`main.py` remains as a thin reference orchestrator (`python main.py <CODE>`);
its HeyGen step is a placeholder — real generation runs through the MCPs.

## Setup

1. Install [Python 3.10+](https://www.python.org/), [Node.js](https://nodejs.org/),
   and [ffmpeg](https://ffmpeg.org/download.html) (ffmpeg/ffprobe on PATH).
2. `pip install openpyxl` (to read `.xlsx` scripts).
3. HeyGen + Higgsfield run as MCP servers inside Claude Code (`/mcp` to
   authenticate) — no API keys stored in this repo.

## Error handling

Every command fails with a clear, actionable message: unknown project, missing
script/sequences/clips, missing composition, missing ffmpeg, render failures
(try `npx hyperframes doctor`).
