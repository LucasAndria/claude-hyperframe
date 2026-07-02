# instruction.md — global AI instructions for producing a video

These instructions apply to EVERY video project. Generate the video using the
settings in the project's `config.json` and the structure in `sequences.json`
(both in `projects/<CODE>/`). Track progress with `python studio.py status`.

## Rule 0 — checklist before anything

**Before ANY generation step, create `projects/<CODE>/CHECKLIST.md`** listing
every task of the production (`python studio.py new` creates it automatically;
if it is missing on an existing project, create it first and tick what is
already done based on `studio.py status`).

**Update the checklist at every step**: tick a task the moment it is finished,
and add sub-tasks as they appear (one line per sequence once `sequences.json`
is filled, retakes, fixes). Never start a generation step without first reading
the checklist, and never finish a step without updating it.

## Production rules

1. **Use the HeyGen MCP to generate the avatar video** (one clip per sequence,
   avatar/voice/aspect from `config.json`).
   - Do NOT add any on-screen text, captions, subtitles, lower thirds,
     graphics, or motion graphics at this stage.

2. **If a scene is incorrect or missing:**
   - Use the Higgsfield MCP to generate a cinematic replacement scene.
   - Keep the same visual style throughout the video: create ONE reference
     still, save it as a reusable Element, and reference it for every scene.

3. **When useful, use the Higgsfield MCP to generate additional B-roll** or
   visual representations to illustrate the narration (the avatar's voice-over
   is always kept over the B-roll).

4. **Once the video is complete** (base assembled with
   `python studio.py build <CODE>` and reviewed), **add motion graphics**:
   author the HyperFrames overlay composition in `public/index.html` following
   `shared/brand.md`, review with frame captures, then produce the final video
   with `python studio.py render <CODE>`.

## Quality gates (do not skip)

- Review every batch of generated clips (mid-frame contact sheet) before the
  next step; regenerate bad takes before assembling.
- Review the assembled base (timeline contact sheet + audio sync) before
  authoring overlays.
- QA the final render (frames at key timestamps, duration, audio) before
  declaring the project TERMINE in the checklist.

## Boundaries

- Everything for a video stays inside `projects/<CODE>/` — never touch another
  project's folder.
- If a HeyGen/Higgsfield MCP tool is missing, reconnect with `/mcp` before
  assuming the capability is unavailable.
