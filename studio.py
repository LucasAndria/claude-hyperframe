#!/usr/bin/env python3
"""studio.py -la commande unique pour les projets video EMO (La Petite Creche).

    python studio.py status                  etat de tous les projets + prochaine etape
    python studio.py new EMO15_VID01         creer un nouveau projet (dossier autonome)
    python studio.py build EMO15_VID01       assembler la video de base (clips -> _1_base.mp4)
    python studio.py render EMO15_VID01      rendre les overlays + remettre l'audio -> video finale

Chaque projet est autonome dans projects/<CODE>/ ; aucune commande ne touche
jamais au dossier d'un autre projet.
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from main import (DEFAULT_CONFIG, PROJECTS_DIR, ROOT, PipelineError, list_videos,
                  load_config, process_with_ffmpeg, resolve_video_dir, stage_motion_assets)

SHARED = ROOT / "shared"

CHECKLIST_TEMPLATE = """# CHECKLIST — {code}

> Regle (voir instruction.md) : cocher chaque tache DES qu'elle est terminee,
> et ajouter les sous-taches decouvertes (une ligne par sequence des que
> sequences.json est rempli, retakes, corrections). Ne jamais lancer une
> generation sans lire cette liste, ni finir une etape sans la mettre a jour.

- [ ] 1. Script valide place dans script.xlsx
- [ ] 2. sequences.json rempli depuis le script (role emy/broll par sequence)
- [ ] 3. Clips HeyGen generes (un par sequence -> heygen_clips/seqNN.mp4)
- [ ] 4. Clips HeyGen relus (contact sheet) — retakes refaits si besoin
- [ ] 5. Still de reference + Element Higgsfield crees (famille visuelle unique)
- [ ] 6. B-roll generes pour chaque sequence broll (higgsfield/clips/brollNN.mp4)
- [ ] 7. B-roll relus — style coherent sur toute la video
- [ ] 8. Base assemblee : python studio.py build {code}
- [ ] 9. Base relue (contact sheet timeline + synchro audio)
- [ ] 10. Motion graphics dans public/index.html (apres validation de la base, charte shared/brand.md)
- [ ] 11. Rendu final : python studio.py render {code}
- [ ] 12. QA finale (frames aux moments cles, duree, audio) -> TERMINE
"""

SEQUENCES_STUB = {
    "title": "",
    "avatar_id": DEFAULT_CONFIG["heygen"]["avatar_id"],
    "voice_id": DEFAULT_CONFIG["heygen"]["voice_id"],
    "fps": 25,
    "sequences": [
        # {"seq": 1, "role": "emy" | "broll", "script": "...", "intention": "...", "visual": "..."}
    ],
}


def run(cmd: list[str], fail_msg: str, use_shell: bool = False) -> None:
    r = subprocess.run(cmd, capture_output=True, text=True, shell=use_shell)
    if r.returncode != 0:
        raise PipelineError(f"{fail_msg}\n{(r.stderr or r.stdout)[-2000:]}")


def ffprobe_dur(p: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(p)], capture_output=True, text=True)
    return float(r.stdout.strip())


def load_sequences(video_dir: Path) -> list[dict]:
    f = video_dir / "sequences.json"
    if not f.exists():
        return []
    return json.loads(f.read_text(encoding="utf-8")).get("sequences", [])


# ---------------------------------------------------------------------------
# new -scaffold a self-contained project folder
# ---------------------------------------------------------------------------
def cmd_new(args) -> int:
    video_dir = PROJECTS_DIR / args.code
    if video_dir.exists():
        raise PipelineError(f"{video_dir} existe deja -on n'y touche pas.")

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

    (video_dir / "CHECKLIST.md").write_text(
        CHECKLIST_TEMPLATE.format(code=args.code), encoding="utf-8")

    # Stage the shared brand assets so every composition starts ready:
    # motion library + style, Montserrat, GSAP.
    public = video_dir / "public"
    stage_motion_assets(public, video_dir, cfg)
    (public / "fonts").mkdir(exist_ok=True)
    for src, dest in ((SHARED / "fonts" / "Montserrat.ttf", public / "fonts" / "Montserrat.ttf"),
                      (SHARED / "vendor" / "gsap.min.js", public / "vendor" / "gsap.min.js")):
        if src.exists():
            shutil.copyfile(src, dest)

    if args.script:
        src = Path(args.script)
        if not src.exists():
            raise PipelineError(f"Script introuvable: {src}")
        shutil.copyfile(src, video_dir / f"script{src.suffix.lower()}")

    print(f"Projet cree: projects/{args.code}/ (checklist: CHECKLIST.md)")
    print(f"  1. Placer le script valide dans projects/{args.code}/script.xlsx"
          + (" (deja copie)" if args.script else ""))
    print(f"  2. Dans Claude Code: \"Remplis sequences.json pour {args.code} a partir du script\"")
    print(f"  3. Suivre l'avancement avec: python studio.py status")
    return 0


# ---------------------------------------------------------------------------
# status -dashboard of every project
# ---------------------------------------------------------------------------
def project_status(video_dir: Path) -> dict:
    name = video_dir.name
    seqs = load_sequences(video_dir)
    n_seq = len(seqs)
    n_broll = sum(1 for s in seqs if s.get("role") == "broll")
    heygen = len(list((video_dir / "heygen_clips").glob("seq*.mp4")))
    broll = len(list((video_dir / "higgsfield" / "clips").glob("broll*.mp4")))
    out = video_dir / "output"
    st = {
        "name": name,
        "script": any(video_dir.glob("script.*")),
        "n_seq": n_seq, "n_broll": n_broll, "heygen": heygen, "broll": broll,
        "base": (out / f"{name}_1_base.mp4").exists(),
        "comp": (video_dir / "public" / "index.html").exists(),
        "final": (out / f"{name}.mp4").exists(),
    }
    if not st["script"]:
        nxt = "ajouter le script (script.xlsx)"
    elif n_seq == 0:
        nxt = "remplir sequences.json (demander a Claude)"
    elif heygen < n_seq:
        nxt = f"generer les clips HeyGen ({heygen}/{n_seq})"
    elif broll < n_broll:
        nxt = f"generer les b-roll Higgsfield ({broll}/{n_broll})"
    elif not st["base"]:
        nxt = f"python studio.py build {name}"
    elif not st["comp"]:
        nxt = "creer les overlays (public/index.html, demander a Claude)"
    elif not st["final"]:
        nxt = f"python studio.py render {name}"
    else:
        nxt = "TERMINE"
    st["next"] = nxt
    return st


def cmd_status(args) -> int:
    codes = [args.code] if args.code else list_videos()
    if not codes:
        print("Aucun projet. Creer le premier: python studio.py new EMO15_VID01")
        return 0
    mark = lambda b: "OK" if b else "--"
    print(f"{'PROJET':<14} {'script':<6} {'seq':<7} {'heygen':<7} {'broll':<6} "
          f"{'base':<5} {'overlays':<8} {'final':<5}  PROCHAINE ETAPE")
    for code in codes:
        st = project_status(resolve_video_dir(code))
        n_seq = str(st["n_seq"]) if st["n_seq"] else "--"
        heygen = "{}/{}".format(st["heygen"], st["n_seq"]) if st["n_seq"] else "--"
        broll = "{}/{}".format(st["broll"], st["n_broll"]) if st["n_broll"] else "--"
        print(f"{st['name']:<14} {mark(st['script']):<6} {n_seq:<7} {heygen:<7} {broll:<6} "
              f"{mark(st['base']):<5} {mark(st['comp']):<8} {mark(st['final']):<5}  {st['next']}")
    return 0


# ---------------------------------------------------------------------------
# build -assemble the edited base video from sequences.json
# ---------------------------------------------------------------------------
def cmd_build(args) -> int:
    video_dir = resolve_video_dir(args.code)
    name = video_dir.name
    cfg = load_config(video_dir)
    seqs = load_sequences(video_dir)
    if not seqs:
        raise PipelineError(f"sequences.json vide ou absent dans projects/{name}/ -le remplir d'abord.")

    vertical = str(cfg.get("orientation", "horizontal")).lower() == "vertical"
    W, H = (1080, 1920) if vertical else (1920, 1080)
    fps = int(cfg.get("hyperframe", {}).get("fps", 25))
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
          f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,fps={fps},format=yuv420p")

    heygen_dir = video_dir / "heygen_clips"
    broll_dir = video_dir / "higgsfield" / "clips"
    work = video_dir / "segments"
    work.mkdir(exist_ok=True)
    out_dir = video_dir / cfg.get("output_dir", "output")
    out_dir.mkdir(exist_ok=True)

    seg_files = []
    for s in seqs:
        n, role = s["seq"], s["role"]
        heygen = heygen_dir / f"seq{n:02d}.mp4"
        if not heygen.exists():
            raise PipelineError(f"Clip HeyGen manquant: {heygen} -generer les clips d'abord.")
        dur = ffprobe_dur(heygen)
        seg = work / f"seg{n:02d}.mp4"
        common = ["-vf", vf, "-r", str(fps),
                  "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
                  "-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "192k",
                  "-t", f"{dur:.3f}", str(seg)]
        if role == "emy":
            cmd = ["ffmpeg", "-y", "-i", str(heygen)] + common
        else:
            broll = broll_dir / f"broll{n:02d}.mp4"
            if not broll.exists():
                raise PipelineError(f"B-roll manquant: {broll} -generer les b-roll d'abord.")
            # video from b-roll (trimmed to dur), audio from heygen (Emy VO)
            cmd = ["ffmpeg", "-y", "-i", str(broll), "-i", str(heygen),
                   "-map", "0:v:0", "-map", "1:a:0"] + common
        run(cmd, f"Echec segment seg{n:02d}")
        print(f"seg{n:02d} [{role:5}] target={dur:.3f}s actual={ffprobe_dur(seg):.3f}s")
        seg_files.append(seg)

    listfile = work / "concat.txt"
    listfile.write_text("".join(f"file '{p.as_posix()}'\n" for p in seg_files), encoding="utf-8")
    base_out = out_dir / f"{name}_1_base.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listfile),
         "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "192k",
         "-movflags", "+faststart", str(base_out)], "Echec de la concatenation")
    print(f"BASE: {base_out} ({ffprobe_dur(base_out):.3f}s)")
    print(f"Prochaine etape: overlays dans public/, puis: python studio.py render {name}")
    return 0


# ---------------------------------------------------------------------------
# render -render the HyperFrames overlays (silent) then mux the base audio
# ---------------------------------------------------------------------------
def cmd_render(args) -> int:
    video_dir = resolve_video_dir(args.code)
    name = video_dir.name
    cfg = load_config(video_dir)
    out_dir = video_dir / cfg.get("output_dir", "output")
    out_dir.mkdir(exist_ok=True)

    base = out_dir / f"{name}_1_base.mp4"
    if not base.exists():
        raise PipelineError(f"Base introuvable: {base} -lancer d'abord: python studio.py build {name}")
    comp = video_dir / (cfg.get("hyperframe", {}).get("composition_dir") or "public")
    if not (comp / "index.html").exists():
        raise PipelineError(f"Pas de composition dans {comp} -creer les overlays d'abord (demander a Claude).")

    # The composition plays the base video full-bleed as public/input-video.mp4 —
    # refresh the copy whenever the base is newer.
    input_vid = comp / "input-video.mp4"
    if not input_vid.exists() or input_vid.stat().st_mtime < base.stat().st_mtime:
        print("Copie de la base dans public/input-video.mp4 ...")
        shutil.copyfile(base, input_vid)

    stage_motion_assets(comp, video_dir, cfg)
    fps = str(cfg.get("hyperframe", {}).get("fps", 25))
    overlay = out_dir / f"{name}_2_overlay.mp4"
    print(f"Rendu HyperFrames (silencieux) -> {overlay.name} ...")
    run(["npx", "hyperframes", "render", str(comp), "-o", str(overlay.resolve()), "--fps", fps],
        "Echec du rendu HyperFrames (essayer: npx hyperframes doctor)",
        use_shell=(sys.platform == "win32"))

    final = out_dir / f"{name}.mp4"
    print(f"Muxage de l'audio de la base -> {final.name} ...")
    process_with_ffmpeg(overlay, final, audio_from=base)
    print(f"FINAL: {final} ({ffprobe_dur(final):.3f}s)")
    return 0


# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(
        prog="studio.py", description="La commande unique pour les projets video EMO.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("new", help="creer un nouveau projet autonome dans projects/<CODE>/")
    p.add_argument("code", help="code du projet, ex. EMO15_VID01")
    p.add_argument("--script", help="chemin du script .xlsx a copier dans le projet")
    p.add_argument("--vertical", action="store_true", help="format 9:16 (defaut: 16:9)")
    p.set_defaults(func=cmd_new)

    p = sub.add_parser("status", help="etat de tous les projets + prochaine etape")
    p.add_argument("code", nargs="?", help="limiter a un projet")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("build", help="assembler la video de base (clips -> _1_base.mp4)")
    p.add_argument("code")
    p.set_defaults(func=cmd_build)

    p = sub.add_parser("render", help="rendre les overlays + remettre l'audio -> video finale")
    p.add_argument("code")
    p.set_defaults(func=cmd_render)

    args = parser.parse_args()
    try:
        return args.func(args)
    except PipelineError as e:
        print(f"ERREUR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
