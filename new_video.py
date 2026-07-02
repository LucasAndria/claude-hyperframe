#!/usr/bin/env python3
"""Scaffold a new self-contained video project under videos/<CODE>/.

Usage:
    python new_video.py EMO15_VID01
    python new_video.py EMO15_VID01 --script "path/to/EMO15_VID01.xlsx"
    python new_video.py EMO15_VID01 --vertical

Creates:
    videos/<CODE>/
        config.json          per-video settings (avatar, voice, fps, orientation)
        script.xlsx          copied in if --script is given
        sequences.json       stub to fill from the script (source of truth)
        public/              HyperFrames composition dir (motion library staged in vendor/)
        heygen_clips/        one clip per sequence (via HeyGen MCP)
        higgsfield/stills/ + higgsfield/clips/   b-roll assets (via Higgsfield MCP)
        source-video/        (alt) drop a pre-recorded base clip here
        output/              rendered results for this video

Nothing outside videos/<CODE>/ is touched: creating a new video never
overwrites or removes another video's files.
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

from main import DEFAULT_CONFIG, ROOT, VIDEOS_DIR, stage_motion_assets

SEQUENCES_STUB = {
    "title": "",
    "avatar_id": DEFAULT_CONFIG["heygen"]["avatar_id"],
    "voice_id": DEFAULT_CONFIG["heygen"]["voice_id"],
    "fps": 25,
    "sequences": [
        # {"seq": 1, "role": "emy" | "broll", "script": "...", "intention": "...", "visual": "..."}
    ],
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold a new video project folder.")
    parser.add_argument("code", help="Video code, e.g. EMO15_VID01")
    parser.add_argument("--script", help="Path to the .xlsx script to copy in as script.xlsx")
    parser.add_argument("--vertical", action="store_true", help="9:16 instead of the default 16:9")
    args = parser.parse_args()

    video_dir = VIDEOS_DIR / args.code
    if video_dir.exists():
        print(f"ERROR: {video_dir} already exists — refusing to touch it.", file=sys.stderr)
        return 1

    for sub in ("public", "heygen_clips", "higgsfield/stills", "higgsfield/clips",
                "source-video", "output"):
        (video_dir / sub).mkdir(parents=True)

    cfg = json.loads(json.dumps(DEFAULT_CONFIG))  # deep copy
    if args.vertical:
        cfg["orientation"] = "vertical"
    (video_dir / "config.json").write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")

    (video_dir / "sequences.json").write_text(
        json.dumps({**SEQUENCES_STUB, "title": args.code}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")

    stage_motion_assets(video_dir / "public", video_dir, cfg)

    if args.script:
        src = Path(args.script)
        if not src.exists():
            print(f"ERROR: script not found: {src}", file=sys.stderr)
            return 1
        shutil.copyfile(src, video_dir / f"script{src.suffix.lower()}")

    print(f"Created {video_dir.relative_to(ROOT)}/")
    for p in sorted(video_dir.rglob("*")):
        print(f"  {p.relative_to(video_dir)}{'/' if p.is_dir() else ''}")
    print("\nNext steps:")
    print(f"  1. Put the validated script at videos/{args.code}/script.xlsx (if not copied)")
    print(f"  2. Fill videos/{args.code}/sequences.json from the script")
    print(f"  3. In Claude Code, generate HeyGen clips + Higgsfield b-roll, then build")
    return 0


if __name__ == "__main__":
    sys.exit(main())
