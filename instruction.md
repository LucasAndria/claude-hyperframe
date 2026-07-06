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

## Rule 1 — validate with the user only when it matters

**Default: keep going.** Chain production steps autonomously, review your own
output at each quality gate (contact sheets, frame captures, durations, audio),
and fix problems yourself. Show the evidence of each step in your progress
updates, but do NOT stop to ask "shall I continue?" between steps.

**Stop and ask for validation ONLY at these moments:**

1. **Before the first spend on a new visual direction** — the Higgsfield
   reference still / Element of a NEW visual family (an existing approved
   Element can be reused without asking), or any deviation from the script,
   voice, avatar, or brand style already on file.
2. **When a result is questionable and fixing it costs credits** — if your own
   review finds a defect (bad take, off-style still, broken framing) whose
   retake spends real money, show it and let the user decide; small no-cost
   fixes you just do.
3. **When the user's instructions leave a real choice open** (format, model
   tier, content changes) — ask once, up front, not mid-run.
4. **After the final render** — the user always does the last QA before the
   project is marked TERMINE in the checklist.

If the user asks for changes at any of these points, apply them, show the
result, and only move on once they confirm.

## Production rules

1. **HeyGen — avatar talking-head clips ONLY.** Use the HeyGen MCP
   (`create_video_from_avatar`, one call per sequence with `role: "emy"`),
   avatar/voice/aspect from `config.json`. Do NOT use HeyGen for b-roll or
   scenery. Do NOT add any on-screen text, captions, subtitles, lower thirds,
   or motion graphics at this stage. Review the clips yourself (contact
   sheet) and redo bad takes before moving on.

2. **Higgsfield — b-roll and replacement scenes ONLY.** Use the Higgsfield
   MCP for every `role: "broll"` sequence and for any scene that is incorrect
   or missing; never for the avatar talking head. Keep one consistent visual
   style: create ONE reference still, save it as a reusable Element
   (a NEW Element needs user validation — Rule 1.1; reusing an approved one
   does not), reference that Element in every per-beat still, then animate
   each still with image-to-video and `generate_audio: false`. The avatar's
   voice-over from the matching HeyGen clip is always kept over the b-roll.

3. **Assemble the base** with `python studio.py build <CODE>` once all clips
   pass your review; check the timeline contact sheet and audio sync.

4. **Add motion graphics last**: author the HyperFrames overlay composition in
   `public/index.html` following `shared/brand.md`, review it with frame
   captures of every beat, then produce the final video with
   `python studio.py render <CODE>`. The final render always goes to the user
   for last QA (Rule 1.4).

## Final video location — keep it apart

**The final video must never sit next to the intermediate videos.** After
`studio.py render`, move the final `<CODE>.mp4` into `projects/<CODE>/final/`
(create the folder if needed). Only intermediates (`<CODE>_1_base.mp4`,
`<CODE>_2_overlay.mp4`) stay in `projects/<CODE>/output/`. When delivering,
always point the user at `final/<CODE>.mp4`.

## Quality gates (do not skip)

- Review every batch of generated clips (mid-frame contact sheet) before the
  next step; regenerate bad takes before assembling.
- Review the assembled base (timeline contact sheet + audio sync) before
  authoring overlays.
- QA the final render (frames at key timestamps, duration, audio) before
  declaring the project TERMINE in the checklist.
- These reviews are yours to run — they do not require user validation unless
  one of the Rule 1 triggers applies. Record each review (and its verdict) in
  the project CHECKLIST.md.

## Boundaries

- Everything for a video stays inside `projects/<CODE>/` — never touch another
  project's folder.
- If a HeyGen/Higgsfield MCP tool is missing, reconnect with `/mcp` before
  assuming the capability is unavailable.
