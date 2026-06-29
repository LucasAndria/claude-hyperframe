#!/usr/bin/env python3
"""Generate the HyperFrames graphic-overlays composition for EMO03_VID01.

Reads captions.json (verbatim SRT cues) and emits public/index.html:
- full-bleed source video with subtle per-shot Ken-Burns push-ins (aligned to
  detected scene cuts; intensity 0.65, no rotation)
- clean warm-editorial lower-third caption track (one card per SRT cue)
- light "La Petite Creche" wordmark (top-left), an intro title, and an outro
  CTA card that hands off cleanly to the source's existing burned-in closing card.
"""
import json
from pathlib import Path

HERE = Path(__file__).parent
W, H, FPS, DUR = 1920, 1080, 25, 203.04

# Scene cuts detected in the source (incl. start + end). Last shot = the source's
# own burned-in "Merci d'avoir regarde" card -> never zoom it.
CUTS = [0, 7.28, 13.04, 14.24, 25.8, 55.36, 63.04, 70.76, 77.04,
        101.68, 112.6, 122.32, 149.04, 169.36, 195.04, 203.04]
PUSH = 0.026  # max scale push (0.04 * intensity 0.65), gentle

# Sparse, meaningful emphasis (accent colour on the key word of a beat).
EMPHASIS = {
    8:  "panique",
    30: "cercle neurologique",
    37: "surcharge",
    38: "sécuriser",
    53: "D’abord",
    54: "ralentis",
    55: "reviens",
    57: "co-régulation",
}

CTA_CUES = (64, 65)  # the "journal des pleurs" download beat


def q(t):
    """Quantize a time to the frame grid."""
    return round(round(t * FPS) / FPS, 4)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def cap_html(text, idx):
    h = esc(text)
    phrase = EMPHASIS.get(idx)
    if phrase:
        p = esc(phrase)
        if p in h:
            h = h.replace(p, f'<span class="em">{p}</span>', 1)
    return h


cues = json.loads((HERE / "captions.json").read_text(encoding="utf-8"))

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
CSS = """
:root{
  --cream: rgba(247,241,229,0.95);
  --cream-solid:#F7F1E5;
  --ink:#2C2620;
  --muted:#6B6258;
  --accent:#BF5700;
  --line: rgba(120,92,60,0.16);
}
*{box-sizing:border-box;}
html,body{
  margin:0;padding:0;width:100%;height:100%;overflow:hidden;background:#000;
  font-family:'Segoe UI','Helvetica Neue',Arial,sans-serif;
}
#stage{position:relative;width:100%;height:100%;overflow:hidden;}

.video-wrapper{position:absolute;left:0;top:0;width:1920px;height:1080px;
  overflow:hidden;transform-origin:50% 46%;will-change:transform;}
.video-wrapper video{width:100%;height:100%;object-fit:cover;}

.card-host{position:absolute;pointer-events:none;}

/* ---- caption band (lower third) ---- */
.cap-host{left:0;top:700px;width:1920px;height:380px;
  display:flex;align-items:flex-end;justify-content:center;padding:0 0 66px 0;}
.cap{
  max-width:1400px;
  background:var(--cream);
  color:var(--ink);
  font-size:37px;line-height:1.34;font-weight:600;
  letter-spacing:.1px;
  text-align:center;
  padding:17px 34px;border-radius:18px;
  border:1px solid var(--line);
  box-shadow:0 10px 34px rgba(0,0,0,0.30), 0 1px 0 rgba(255,255,255,0.45) inset;
}
.cap .em{color:var(--accent);font-weight:700;}

/* ---- wordmark ---- */
.brand-host{left:46px;top:40px;width:520px;height:72px;}
.brand{display:inline-flex;align-items:center;gap:12px;
  padding:9px 18px 9px 16px;border-radius:999px;
  background:rgba(20,16,12,0.30);
  border:1px solid rgba(255,255,255,0.16);}
.brand .dot{width:11px;height:11px;border-radius:50%;background:var(--accent);
  box-shadow:0 0 0 4px rgba(191,87,0,0.22);}
.brand .name{font-family:Georgia,'Times New Roman',serif;font-style:italic;
  font-size:30px;color:#FBF6EC;letter-spacing:.3px;
  text-shadow:0 1px 3px rgba(0,0,0,0.5);}

/* ---- intro title ---- */
.intro-host{left:0;top:120px;width:1920px;height:300px;
  display:flex;flex-direction:column;align-items:center;justify-content:flex-start;}
.intro .kicker{font-size:23px;font-weight:700;letter-spacing:6px;
  color:#F7E7CF;text-shadow:0 2px 8px rgba(0,0,0,0.55);}
.intro .title{font-family:Georgia,'Times New Roman',serif;
  font-size:92px;font-weight:700;color:#FFFFFF;margin-top:14px;
  text-shadow:0 4px 22px rgba(0,0,0,0.6);}
.intro .rule{width:0;height:4px;background:var(--accent);border-radius:3px;margin-top:20px;}

/* ---- outro CTA (upper-right, clear of the presenter's face; hands off to source's own end card) ---- */
.cta-host{left:0;top:64px;width:1920px;height:300px;
  display:flex;align-items:flex-start;justify-content:flex-end;padding-right:60px;}
.cta{display:flex;align-items:center;gap:20px;
  background:var(--cream-solid);color:var(--ink);
  padding:22px 30px;border-radius:20px;
  border:1px solid var(--line);
  box-shadow:0 16px 44px rgba(0,0,0,0.34);max-width:560px;}
.cta .glyph{flex:0 0 auto;width:64px;height:64px;border-radius:16px;
  background:var(--accent);display:flex;align-items:center;justify-content:center;
  color:#fff;font-size:34px;font-weight:700;}
.cta .ctext .k{font-size:20px;font-weight:700;letter-spacing:3px;color:var(--accent);}
.cta .ctext .t{font-size:38px;font-weight:700;line-height:1.2;margin-top:4px;}
.cta .ctext .s{font-size:24px;color:var(--muted);margin-top:4px;}
"""

# ---------------------------------------------------------------------------
# BODY
# ---------------------------------------------------------------------------
body = []
body.append(f'''  <div class="video-wrapper" id="video-wrap">
    <video id="bg-video" src="input-video.mp4" muted playsinline
           data-start="0" data-duration="{DUR}" data-track-index="1"></video>
  </div>''')

# wordmark (appears after the intro fades; off before the source end card)
body.append(f'''  <div class="card-host brand-host clip" data-card-id="brand"
       data-start="{q(4.8)}" data-duration="{q(195.0-4.8)}" data-track-index="5"
       style="visibility:hidden;opacity:0;">
    <div class="brand"><span class="dot"></span><span class="name">La Petite Crèche</span></div>
  </div>''')

# intro title
body.append(f'''  <div class="card-host intro-host clip" data-card-id="intro"
       data-start="0" data-duration="{q(4.9)}" data-track-index="4"
       style="visibility:hidden;opacity:0;">
    <div class="intro">
      <div class="kicker" id="intro-k">LA PETITE CRÈCHE</div>
      <div class="title" id="intro-t">Pleurs prolongés</div>
      <div class="rule" id="intro-r"></div>
    </div>
  </div>''')

# caption cards
for c in cues:
    idx, s, e = c["i"], c["start"], c["end"]
    hid = f"cap-{idx:02d}"
    dur = round(e - s, 3)
    body.append(f'''  <div class="card-host cap-host clip" data-card-id="{hid}"
       data-start="{s}" data-duration="{dur}" data-track-index="2"
       style="visibility:hidden;opacity:0;">
    <div class="cap">{cap_html(c["text"], idx)}</div>
  </div>''')

# outro CTA (spans cue 64 start .. cue 65 end)
cta_start = next(c["start"] for c in cues if c["i"] == CTA_CUES[0])
cta_end = next(c["end"] for c in cues if c["i"] == CTA_CUES[1])
body.append(f'''  <div class="card-host cta-host clip" data-card-id="cta"
       data-start="{cta_start}" data-duration="{round(cta_end-cta_start,3)}" data-track-index="3"
       style="visibility:hidden;opacity:0;">
    <div class="cta">
      <div class="glyph">&#8595;</div>
      <div class="ctext">
        <div class="k">À TÉLÉCHARGER</div>
        <div class="t">Le journal des pleurs</div>
        <div class="s">Lien en description</div>
      </div>
    </div>
  </div>''')

# ---------------------------------------------------------------------------
# TIMELINE (GSAP)
# ---------------------------------------------------------------------------
js = []
js.append("const tl = window.gsap.timeline({ paused: true });")

# --- per-shot Ken-Burns ---
js.append("// per-shot gentle push-ins (reset at each cut; no rotation)")
js.append("tl.set('#video-wrap', { scale: 1.0 }, 0);")
for k in range(len(CUTS) - 1):
    a, b = CUTS[k], CUTS[k + 1]
    dur = b - a
    is_last = (k == len(CUTS) - 2)
    qa = q(a)
    if is_last or dur < 4.0:
        js.append(f"tl.set('#video-wrap', {{ scale: 1.0 }}, {qa});")
    else:
        js.append(f"tl.set('#video-wrap', {{ scale: 1.0 }}, {qa});")
        js.append(f"tl.to('#video-wrap', {{ scale: {1.0+PUSH:.3f}, duration: {dur:.3f}, ease: 'sine.inOut' }}, {qa});")


def enter(hid, t, dur_in=0.18, rise=8):
    s = []
    t = q(t)
    s.append(f"tl.set('.card-host[data-card-id=\"{hid}\"]', {{ visibility: 'visible' }}, {t});")
    s.append(f"tl.fromTo('.card-host[data-card-id=\"{hid}\"]', {{ opacity: 0, y: {rise} }}, {{ opacity: 1, y: 0, duration: {dur_in}, ease: 'power2.out' }}, {t});")
    return s


def leave(hid, t_end, dur_out=0.16):
    s = []
    t0 = q(t_end - dur_out)
    te = q(t_end)
    s.append(f"tl.to('.card-host[data-card-id=\"{hid}\"]', {{ opacity: 0, duration: {dur_out}, ease: 'power2.in' }}, {t0});")
    s.append(f"tl.set('.card-host[data-card-id=\"{hid}\"]', {{ visibility: 'hidden' }}, {te});")
    return s


# --- wordmark (after intro) ---
js.append("// wordmark")
js += enter("brand", 5.0, dur_in=0.8, rise=0)
js.append("tl.to('.card-host[data-card-id=\"brand\"]', { opacity: 0.92, duration: 0.01 }, %s);" % q(5.8))
js += leave("brand", 195.0, dur_out=0.5)

# --- intro ---
js.append("// intro title")
js += enter("intro", 0.3, dur_in=0.6, rise=14)
js.append("tl.fromTo('.card[data-card-id=\"intro\"] #intro-t', { opacity:0, y:18 }, { opacity:1, y:0, duration:0.7, ease:'power3.out' }, %s);" % q(0.5))
js.append("tl.fromTo('#intro-r', { width:0 }, { width:120, duration:0.6, ease:'power2.out' }, %s);" % q(0.9))
js += leave("intro", 4.9, dur_out=0.6)

# --- captions ---
js.append("// captions")
for c in cues:
    idx, s, e = c["i"], c["start"], c["end"]
    hid = f"cap-{idx:02d}"
    dur_in = 0.18 if (e - s) > 0.9 else 0.12
    dur_out = 0.16 if (e - s) > 0.9 else 0.1
    js += enter(hid, s, dur_in=dur_in)
    # subtle accent pop for emphasis cues
    if idx in EMPHASIS:
        js.append(f"tl.fromTo('.card[data-card-id=\"{hid}\"] .em', {{ scale:0.92 }}, {{ scale:1.0, duration:0.34, ease:'back.out(2)', transformOrigin:'50% 60%' }}, {q(s+dur_in)});")
    js += leave(hid, e, dur_out=dur_out)

# --- outro CTA ---
js.append("// outro CTA")
js += enter("cta", cta_start, dur_in=0.4, rise=16)
js += leave("cta", cta_end, dur_out=0.45)

js.append('window.__timelines = window.__timelines || {};')
js.append('window.__timelines["graphic-overlays"] = tl;')

JS = "\n          ".join(js)

# ---------------------------------------------------------------------------
# ASSEMBLE
# ---------------------------------------------------------------------------
html = f'''<!doctype html>
<html lang="fr">
  <head>
    <meta charset="utf-8" />
    <style>{CSS}</style>
  </head>
  <body>
    <div id="stage"
      data-composition-id="graphic-overlays"
      data-start="0"
      data-duration="{DUR}"
      data-fps="{FPS}"
      data-width="{W}"
      data-height="{H}">
{chr(10).join(body)}

      <script src="vendor/gsap.min.js"></script>
      <script>
        (function () {{
          {JS}
        }})();
      </script>
    </div>
  </body>
</html>
'''

out = HERE / "public" / "index.html"
out.write_text(html, encoding="utf-8")
print(f"Wrote {out} ({len(html)} bytes)")
print(f"Captions: {len(cues)} | shots: {len(CUTS)-1} | CTA window: {cta_start}-{cta_end}s")
