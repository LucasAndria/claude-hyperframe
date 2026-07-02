#!/usr/bin/env python3
"""Assemble the edited base video for EMO14_VID01.

For each of the 19 sequences:
  - role 'emy'   -> use the HeyGen talking-head clip as-is (video + Emy audio).
  - role 'broll' -> use the Higgsfield b-roll video, trimmed to the HeyGen clip's
                    exact duration, with the HeyGen clip's audio (Emy VO) muxed in.
All segments are normalised to 1920x1080 / 25fps / h264 yuv420p / aac 48k stereo,
then concatenated into <this video folder>/output/<CODE>_1_base.mp4.
"""
import json, subprocess, sys
from pathlib import Path

BASE = Path(__file__).parent                      # projects/<CODE>
HEYGEN = BASE / "heygen_clips"
BROLL = BASE / "higgsfield" / "clips"
WORK = BASE / "segments"
WORK.mkdir(exist_ok=True)
OUT = BASE / "output"
OUT.mkdir(exist_ok=True)

W, H, FPS = 1920, 1080, 25

seqs = json.loads((BASE / "sequences.json").read_text(encoding="utf-8"))["sequences"]

def ffprobe_dur(p: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(p)], capture_output=True, text=True)
    return float(r.stdout.strip())

VF = f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,fps={FPS},format=yuv420p"

seg_files = []
for s in seqs:
    n = s["seq"]
    role = s["role"]
    heygen = HEYGEN / f"seq{n:02d}.mp4"
    dur = ffprobe_dur(heygen)
    seg = WORK / f"seg{n:02d}.mp4"
    if role == "emy":
        cmd = ["ffmpeg", "-y", "-i", str(heygen),
               "-vf", VF, "-r", str(FPS),
               "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "192k",
               "-t", f"{dur:.3f}", str(seg)]
    else:
        broll = BROLL / f"broll{n:02d}.mp4"
        # video from b-roll (trimmed to dur), audio from heygen (Emy VO)
        cmd = ["ffmpeg", "-y", "-i", str(broll), "-i", str(heygen),
               "-map", "0:v:0", "-map", "1:a:0",
               "-vf", VF, "-r", str(FPS),
               "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "192k",
               "-t", f"{dur:.3f}", str(seg)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"FAIL seg{n:02d}:\n{r.stderr[-1500:]}", file=sys.stderr)
        sys.exit(1)
    actual = ffprobe_dur(seg)
    print(f"seg{n:02d} [{role:5}] target={dur:.3f}s actual={actual:.3f}s")
    seg_files.append(seg)

# concat
listfile = WORK / "concat.txt"
listfile.write_text("".join(f"file '{p.as_posix()}'\n" for p in seg_files), encoding="utf-8")
base_out = OUT / f"{BASE.name}_1_base.mp4"
cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listfile),
       "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "192k",
       "-movflags", "+faststart", str(base_out)]
r = subprocess.run(cmd, capture_output=True, text=True)
if r.returncode != 0:
    print(f"CONCAT FAIL:\n{r.stderr[-2000:]}", file=sys.stderr)
    sys.exit(1)
print("BASE:", base_out, f"{ffprobe_dur(base_out):.3f}s")
