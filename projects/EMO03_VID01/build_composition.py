#!/usr/bin/env python3
"""Generate the HyperFrames graphic-overlays composition for EMO03_VID01 (v2).

Reads captions.json (verbatim SRT cues) and emits public/index.html:
- full-bleed source video with subtle per-shot Ken-Burns push-ins
- NEW caption style: bold rounded-geometric (Montserrat 800), white with warm-amber
  emphasis words, NO background box, centered mid-lower, broken into short 3-4 word
  chunks that pop in sequence (reference / social style)
- narration-synced motion-design beats (added in build_motion.py overlay, soft palette,
  motion-example vocabulary)
- light "La Petite Creche" wordmark, an intro title, and an outro CTA card.

Soft warm palette is preserved throughout (cream / ink / burnt-orange).
"""
import json
import re
import unicodedata
from pathlib import Path

HERE = Path(__file__).parent
W, H, FPS, DUR = 1920, 1080, 25, 203.04

# Scene cuts detected in the source (incl. start + end). Last shot = the source's
# own burned-in "Merci d'avoir regarde" card -> never zoom it.
CUTS = [0, 7.28, 13.04, 14.24, 25.8, 55.36, 63.04, 70.76, 77.04,
        101.68, 112.6, 122.32, 149.04, 169.36, 195.04, 203.04]
PUSH = 0.026  # max scale push (0.04 * intensity 0.65), gentle

# Words that get the warm-amber accent wherever they appear (meaningful key beats).
# Accent-insensitive match on the word core (punctuation stripped).
EMPH_WORDS = {
    "panique", "alarme", "biologique", "automatique", "fréquent", "fréquente",
    "surcharge", "sécuriser", "sécurité", "sécurises", "calme", "co-régulation",
    "cercle", "neurologique", "respire", "respires", "respiration", "d'abord",
    "ensuite", "puis", "reviens", "ralentis", "seul", "protection", "immature",
}

# Caption chunking
MAX_WORDS = 4
MAX_CHARS = 26
MIN_CHUNK = 0.45  # s, soft floor for a chunk's visible time

CTA_CUES = (64, 65)  # the "journal des pleurs" download beat


def q(t):
    """Quantize a time to the frame grid."""
    return round(round(t * FPS) / FPS, 4)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _norm(w):
    """Lowercase + strip accents + strip surrounding punctuation for matching."""
    w = w.strip(" \t\n\r.,!?;:…«»\"'’()-")
    w = unicodedata.normalize("NFD", w.lower())
    w = "".join(c for c in w if unicodedata.category(c) != "Mn")
    return w


_EMPH_NORM = {_norm(w) for w in EMPH_WORDS}


def emphasize(text):
    """Wrap accent words in <span class="em">, escaping the rest."""
    out = []
    for tok in text.split(" "):
        if not tok:
            continue
        # peel leading/trailing punctuation so the span hugs the word
        m = re.match(r'^([^\wÀ-ÿ’\'-]*)(.*?)([^\wÀ-ÿ’\'-]*)$', tok, re.UNICODE)
        lead, core, trail = m.group(1), m.group(2), m.group(3)
        if core and _norm(core) in _EMPH_NORM:
            out.append(esc(lead) + f'<span class="em">{esc(core)}</span>' + esc(trail))
        else:
            out.append(esc(tok))
    return " ".join(out)


def chunk_cue(text):
    """Split a cue's text into short word-groups (<= MAX_WORDS / MAX_CHARS)."""
    words = text.split()
    chunks, cur = [], []
    for w in words:
        trial = cur + [w]
        if cur and (len(trial) > MAX_WORDS or len(" ".join(trial)) > MAX_CHARS):
            chunks.append(" ".join(cur))
            cur = [w]
        else:
            cur = trial
    if cur:
        chunks.append(" ".join(cur))
    return chunks


def build_chunks(cues):
    """Flatten cues -> timed chunks. Each cue's span is split across its chunks,
    weighted by word count, so the reveal cadence tracks the speech."""
    out = []
    for c in cues:
        s, e = c["start"], c["end"]
        groups = chunk_cue(c["text"])
        weights = [max(1, len(g.split())) for g in groups]
        total_w = sum(weights)
        span = e - s
        t = s
        for g, w in zip(groups, weights):
            d = span * (w / total_w)
            out.append({"text": g, "start": round(t, 3), "end": round(t + d, 3),
                        "cue": c["i"]})
            t += d
        # snap last chunk end to the cue end (avoid drift)
        out[-1]["end"] = round(e, 3)
    return out


cues = json.loads((HERE / "captions.json").read_text(encoding="utf-8"))
chunks = build_chunks(cues)

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
CSS = """
@font-face{
  font-family:'Montserrat';font-style:normal;font-weight:100 900;
  font-display:block;src:url('vendor/fonts/Montserrat.ttf') format('truetype');
}
:root{
  --cream: rgba(247,241,229,0.95);
  --cream-solid:#F7F1E5;
  --ink:#2C2620;
  --muted:#6B6258;
  --accent:#BF5700;       /* solid UI on cream */
  --hi:#F4982E;           /* warm-amber caption highlight, legible on video */
  --line: rgba(120,92,60,0.16);
}
*{box-sizing:border-box;}
html,body{
  margin:0;padding:0;width:100%;height:100%;overflow:hidden;background:#000;
  font-family:'Montserrat','Segoe UI',Arial,sans-serif;
}
#stage{position:relative;width:100%;height:100%;overflow:hidden;}

.video-wrapper{position:absolute;left:0;top:0;width:1920px;height:1080px;
  overflow:hidden;transform-origin:50% 46%;will-change:transform;}
.video-wrapper video{width:100%;height:100%;object-fit:cover;}

.card-host{position:absolute;pointer-events:none;}

/* ---- captions: bold word-chunks, no box, centered mid-lower ---- */
.cap-host{left:0;top:640px;width:1920px;height:300px;
  display:flex;align-items:flex-start;justify-content:center;}
.cap{
  max-width:1480px;text-align:center;
  font-family:'Montserrat','Segoe UI',Arial,sans-serif;
  font-weight:800;font-size:66px;line-height:1.14;letter-spacing:.2px;
  color:#FFFFFF;
  padding:0 64px;
  text-shadow:0 3px 12px rgba(0,0,0,0.55), 0 1px 2px rgba(0,0,0,0.72);
  -webkit-text-stroke:0.6px rgba(20,12,4,0.28);
  will-change:transform,opacity;
}
.cap .em{color:var(--hi);text-shadow:0 3px 12px rgba(0,0,0,0.55),0 0 2px rgba(0,0,0,0.7);}

/* ---- wordmark ---- */
.brand-host{left:46px;top:40px;width:560px;height:72px;}
.brand{display:inline-flex;align-items:center;gap:12px;
  padding:9px 20px 9px 16px;border-radius:999px;
  background:rgba(20,16,12,0.30);
  border:1px solid rgba(255,255,255,0.16);}
.brand .dot{width:11px;height:11px;border-radius:50%;background:var(--hi);
  box-shadow:0 0 0 4px rgba(244,152,46,0.22);}
.brand .name{font-family:'Montserrat','Segoe UI',Arial,sans-serif;font-weight:700;font-style:normal;
  font-size:27px;color:#FBF6EC;letter-spacing:.3px;
  text-shadow:0 1px 3px rgba(0,0,0,0.5);}

/* ---- intro title ---- */
.intro-host{left:0;top:150px;width:1920px;height:480px;
  display:flex;flex-direction:column;align-items:center;justify-content:flex-start;}
.intro .kicker{font-family:'Montserrat','Segoe UI',Arial,sans-serif;font-size:24px;font-weight:700;letter-spacing:8px;
  color:#FBEAD0;text-shadow:0 2px 10px rgba(0,0,0,0.6);}
.intro .title{font-family:'Montserrat','Segoe UI',Arial,sans-serif;
  font-size:108px;font-weight:800;color:#FFFFFF;margin-top:16px;letter-spacing:.5px;
  text-shadow:0 6px 26px rgba(0,0,0,0.62);}
.intro .rule{width:0;height:6px;background:var(--hi);border-radius:4px;margin-top:24px;
  box-shadow:0 2px 10px rgba(244,152,46,0.5);}

/* ---- outro CTA ---- */
.cta-host{left:0;top:64px;width:1920px;height:300px;
  display:flex;align-items:flex-start;justify-content:flex-end;padding-right:60px;}
.cta{display:flex;align-items:center;gap:20px;
  background:var(--cream-solid);color:var(--ink);
  padding:22px 30px;border-radius:22px;
  border:1px solid var(--line);
  box-shadow:0 16px 44px rgba(0,0,0,0.34);max-width:580px;}
.cta .glyph{flex:0 0 auto;width:64px;height:64px;border-radius:16px;
  background:var(--accent);display:flex;align-items:center;justify-content:center;
  color:#fff;font-size:34px;font-weight:700;}
.cta .ctext .k{font-size:20px;font-weight:800;letter-spacing:3px;color:var(--accent);}
.cta .ctext .t{font-size:38px;font-weight:800;line-height:1.2;margin-top:4px;}
.cta .ctext .s{font-size:24px;font-weight:600;color:var(--muted);margin-top:4px;}

/* ============ motion-design beats (soft palette, motion-example vocabulary) ============ */
.mg-host{position:absolute;pointer-events:none;font-family:'Montserrat','Segoe UI',Arial,sans-serif;}
.mg-panel{background:rgba(247,241,229,0.94);border:1px solid var(--line);border-radius:22px;
  box-shadow:0 18px 48px rgba(0,0,0,0.32), 0 1px 0 rgba(255,255,255,0.55) inset;color:var(--ink);}
.mg-k{font-weight:800;letter-spacing:2.5px;font-size:18px;color:var(--accent);text-transform:uppercase;}
.mg-row{display:flex;align-items:center;gap:14px;}
.mg-amber{color:var(--accent);font-weight:800;}
.mg-line{stroke:var(--accent);stroke-width:5;fill:none;stroke-linecap:round;stroke-linejoin:round;}
.mg-ico{flex:0 0 auto;}

/* M1 heart-rate chip */
.ecg-host{left:1408px;top:96px;width:436px;height:158px;}
.ecg-title{font-weight:800;font-size:21px;color:var(--ink);}

/* M2 stress trio */
.trio-host{left:78px;top:168px;width:540px;height:312px;}
.trio-row{display:flex;align-items:center;gap:16px;padding:11px 0;}
.trio-row + .trio-row{border-top:1px solid var(--line);}
.trio-name{font-weight:700;font-size:27px;color:var(--ink);}
.trio-tag{margin-left:auto;font-weight:800;font-size:26px;color:var(--accent);}

/* M3 circle of co-regulation */
.circ-host{left:1268px;top:104px;width:640px;height:600px;display:flex;flex-direction:column;align-items:center;}
.circ-node{font-weight:800;font-size:26px;color:var(--ink);background:var(--cream-solid);
  border:2px solid var(--accent);border-radius:999px;padding:10px 26px;
  box-shadow:0 8px 22px rgba(0,0,0,0.22);}
.circ-cap{margin-top:44px;font-weight:800;font-size:31px;color:#FFFFFF;text-align:center;line-height:1.2;
  text-shadow:0 3px 12px rgba(0,0,0,0.6), 0 1px 2px rgba(0,0,0,0.72);}
.circ-cap .mg-amber{color:var(--hi);text-shadow:0 3px 12px rgba(0,0,0,0.6);}

/* M4 breathing pacer */
.breathe-host{left:1360px;top:170px;width:470px;height:470px;display:flex;align-items:center;justify-content:center;}
.breathe-label{position:absolute;font-weight:800;font-size:34px;color:#FFFFFF;
  text-shadow:0 3px 12px rgba(0,0,0,0.5);letter-spacing:1px;}

/* M5 three-step checklist */
.steps-host{left:980px;top:176px;width:880px;height:560px;}
.steps-card{padding:30px 34px;}
.steps-k{font-weight:800;letter-spacing:3px;font-size:20px;color:var(--accent);text-transform:uppercase;margin-bottom:18px;}
.step-row{display:flex;align-items:center;gap:20px;padding:13px 0;}
.step-row + .step-row{border-top:1px solid var(--line);}
.step-num{flex:0 0 auto;width:46px;height:46px;border-radius:12px;background:rgba(191,87,0,0.12);
  color:var(--accent);font-weight:800;font-size:24px;display:flex;align-items:center;justify-content:center;}
.step-txt{font-weight:700;font-size:32px;color:var(--ink);}
.step-check{margin-left:auto;}
.steps-result{margin-top:20px;text-align:center;font-weight:800;font-size:40px;color:var(--accent);
  letter-spacing:.5px;}

/* ---- full-bleed illustrative cutaways (Higgsfield-generated) ---- */
.cut-host{left:0;top:0;width:1920px;height:1080px;}
.cut-zoom{position:absolute;left:0;top:0;width:1920px;height:1080px;transform-origin:50% 50%;will-change:transform;}
.cut-media{position:absolute;left:0;top:0;width:1920px;height:1080px;object-fit:cover;}
.cut-scrim{position:absolute;left:0;top:0;width:1920px;height:1080px;
  background:linear-gradient(180deg, rgba(18,12,6,0.14) 0%, rgba(18,12,6,0.0) 28%, rgba(18,12,6,0.16) 58%, rgba(18,12,6,0.48) 100%);}
.cut-scrim-coreg{background:linear-gradient(180deg, rgba(18,12,6,0.05) 0%, rgba(18,12,6,0.0) 24%, rgba(18,12,6,0.32) 54%, rgba(18,12,6,0.60) 100%);}
"""

# ---------------------------------------------------------------------------
# BODY
# ---------------------------------------------------------------------------
body = []
body.append(f'''  <div class="video-wrapper" id="video-wrap">
    <video id="bg-video" src="input-video.mp4" muted playsinline
           data-start="0" data-duration="{DUR}" data-track-index="1"></video>
  </div>''')

# full-bleed illustrative cutaways (track 2/3: above video, below captions + panels)
body.append('''  <div class="card-host cut-host clip" data-card-id="cut-3am"
       data-start="25.8" data-duration="4.3" data-track-index="2" style="visibility:hidden;opacity:0;">
    <div class="cut-zoom" id="cz-3am"><img class="cut-media" src="assets/illu-3am.png" /></div>
    <div class="cut-scrim"></div>
  </div>''')
body.append('''  <div class="card-host cut-host clip" data-card-id="cut-scene"
       data-start="149.04" data-duration="20.32" data-track-index="2" style="visibility:hidden;opacity:0;">
    <div class="cut-zoom" id="cz-scene"><img class="cut-media" src="assets/scene-calm.jpg" /></div>
    <div class="cut-scrim"></div>
  </div>''')
body.append('''  <div class="card-host cut-host clip" data-card-id="cut-coreg"
       data-start="169.5" data-duration="7.0" data-track-index="3" style="visibility:hidden;opacity:0;">
    <div class="cut-zoom" id="cz-coreg"><img class="cut-media" src="assets/illu-coreg.png" /></div>
    <div class="cut-scrim cut-scrim-coreg"></div>
  </div>''')

# intro title (brand wordmark + "La Petite Crèche" eyebrow removed per request)
body.append(f'''  <div class="card-host intro-host clip" data-card-id="intro"
       data-start="0" data-duration="{q(4.9)}" data-track-index="6"
       style="visibility:hidden;opacity:0;">
    <div class="intro">
      <div class="title" id="intro-t">Pleurs prolongés</div>
      <div class="rule" id="intro-r"></div>
    </div>
  </div>''')

# NOTE: the bottom word-chunk subtitle track has been removed per request.
# (build_chunks/emphasize remain available if it ever needs to come back.)

# ---------------------------------------------------------------------------
# motion-design beats (soft palette, motion-example vocabulary)
# ---------------------------------------------------------------------------
HEART = '<path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" fill="#BF5700"/>'
WAVE = '<path class="mg-line" style="stroke-width:3" d="M3 15 q3.7 -9 7.5 0 t7.5 0 t7.5 0"/>'
BULB = '<path d="M9 21h6v-1H9v1zm3-19a7 7 0 0 0-4 12.74V17h8v-2.26A7 7 0 0 0 12 2z" fill="#BF5700"/>'

# M1 — heart-rate / alarm chip (panic rising, ~14.4-25.4s)
body.append(f'''  <div class="mg-host ecg-host clip" data-card-id="mg-ecg"
       data-start="14.4" data-duration="11.0" data-track-index="8"
       style="visibility:hidden;opacity:0;">
    <div class="mg-panel" style="padding:18px 22px;">
      <div class="mg-row">
        <svg class="mg-ico" width="28" height="28" viewBox="0 0 24 24">{HEART}</svg>
        <span class="ecg-title">Rythme cardiaque</span>
        <span class="mg-amber" id="ecg-arrow" style="margin-left:auto;font-size:28px;">&#8593;</span>
      </div>
      <svg width="396" height="74" viewBox="0 0 396 74" style="margin-top:10px;">
        <polyline id="ecg-line" class="mg-line"
          points="0,44 44,44 64,44 80,14 96,68 116,44 156,44 176,18 192,64 212,44 252,44 272,44 288,14 304,68 324,44 364,44 396,44"/>
      </svg>
    </div>
  </div>''')

# M2 — stress-response trio (~42-50.4s)
body.append(f'''  <div class="mg-host trio-host clip" data-card-id="mg-trio"
       data-start="42.0" data-duration="8.4" data-track-index="9"
       style="visibility:hidden;opacity:0;">
    <div class="mg-panel" style="padding:22px 28px;">
      <div class="mg-k" style="margin-bottom:6px;">Quand l&rsquo;alarme monte</div>
      <div class="trio-row" id="trio-1">
        <svg class="mg-ico" width="32" height="32" viewBox="0 0 24 24">{HEART}</svg>
        <span class="trio-name">Rythme cardiaque</span><span class="trio-tag">&#8593;</span>
      </div>
      <div class="trio-row" id="trio-2">
        <svg class="mg-ico" width="32" height="32" viewBox="0 0 30 30">{WAVE}</svg>
        <span class="trio-name">Respiration courte</span><span class="trio-tag">&#8595;</span>
      </div>
      <div class="trio-row" id="trio-3">
        <svg class="mg-ico" width="32" height="32" viewBox="0 0 24 24">{BULB}</svg>
        <span class="trio-name">Clart&eacute; mentale</span><span class="trio-tag">&#8595;</span>
      </div>
    </div>
  </div>''')

# M3 — circle of co-regulation (~70.7-77.0s, "cercle neurologique")
body.append('''  <div class="mg-host circ-host clip" data-card-id="mg-circ"
       data-start="70.7" data-duration="6.4" data-track-index="10"
       style="visibility:hidden;opacity:0;">
    <div style="position:relative;width:420px;height:420px;">
      <svg width="420" height="420" viewBox="0 0 420 420">
        <circle id="circ-ring" cx="210" cy="210" r="135" fill="none" stroke="#BF5700"
          stroke-width="6" stroke-linecap="round" stroke-dasharray="848" stroke-dashoffset="848"/>
        <path d="M345 197 l15 13 l-17 9 z" fill="#BF5700"/>
        <path d="M75 223 l-15 -13 l17 -9 z" fill="#BF5700"/>
        <g id="circ-dot"><circle cx="210" cy="75" r="11" fill="#BF5700"/></g>
      </svg>
      <div class="circ-node" style="position:absolute;left:50%;top:6px;transform:translate(-50%,-50%);">PARENT</div>
      <div class="circ-node" style="position:absolute;left:50%;top:414px;transform:translate(-50%,-50%);">B&Eacute;B&Eacute;</div>
    </div>
    <div class="circ-cap">Parent et b&eacute;b&eacute; se r&eacute;gulent<br><span class="mg-amber">ensemble</span></div>
  </div>''')

# M4 — breathing pacer (~112.6-122.2s, "respire lentement")
body.append('''  <div class="mg-host breathe-host clip" data-card-id="mg-breathe"
       data-start="112.6" data-duration="9.6" data-track-index="11"
       style="visibility:hidden;opacity:0;">
    <div style="position:relative;width:360px;height:360px;display:flex;align-items:center;justify-content:center;">
      <svg width="360" height="360" viewBox="0 0 360 360" style="position:absolute;left:0;top:0;">
        <circle id="breathe-c2" cx="180" cy="180" r="150" fill="rgba(244,152,46,0.10)" stroke="rgba(244,152,46,0.55)" stroke-width="2"/>
        <circle id="breathe-c1" cx="180" cy="180" r="98" fill="rgba(247,241,229,0.20)" stroke="#F4982E" stroke-width="4"/>
      </svg>
      <div class="breathe-label">Respire</div>
    </div>
  </div>''')

# M5 — three-step checklist (~152.6-167.0s, "D'abord / Ensuite / Puis -> co-régulation")
CHK = '<svg class="step-check" id="check-{n}" width="42" height="42" viewBox="0 0 24 24"><path class="chk" d="M5 13l4 4L19 7" fill="none" stroke="#BF5700" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>'
body.append(f'''  <div class="mg-host steps-host clip" data-card-id="mg-steps"
       data-start="152.6" data-duration="14.4" data-track-index="12"
       style="visibility:hidden;opacity:0;">
    <div class="mg-panel steps-card">
      <div class="steps-k">Revenir au calme &mdash; 3 temps</div>
      <div class="step-row" id="step-1">
        <div class="step-num">1</div><div class="step-txt">S&eacute;curiser ton b&eacute;b&eacute;</div>{CHK.format(n=1)}
      </div>
      <div class="step-row" id="step-2">
        <div class="step-num">2</div><div class="step-txt">Ralentir ton corps</div>{CHK.format(n=2)}
      </div>
      <div class="step-row" id="step-3">
        <div class="step-num">3</div><div class="step-txt">Revenir, voix douce</div>{CHK.format(n=3)}
      </div>
      <div class="steps-result" id="steps-res">= CO-R&Eacute;GULATION</div>
    </div>
  </div>''')

# outro CTA
cta_start = next(c["start"] for c in cues if c["i"] == CTA_CUES[0])
cta_end = next(c["end"] for c in cues if c["i"] == CTA_CUES[1])
body.append(f'''  <div class="card-host cta-host clip" data-card-id="cta"
       data-start="{cta_start}" data-duration="{round(cta_end-cta_start,3)}" data-track-index="13"
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
    js.append(f"tl.set('#video-wrap', {{ scale: 1.0 }}, {qa});")
    if not (is_last or dur < 4.0):
        js.append(f"tl.to('#video-wrap', {{ scale: {1.0+PUSH:.3f}, duration: {dur:.3f}, ease: 'sine.inOut' }}, {qa});")


def sel(hid):
    return f'.card-host[data-card-id="{hid}"]'


# --- intro ---
js.append("// intro title")
js.append(f"tl.set('{sel('intro')}', {{ visibility:'visible' }}, 0.3);")
js.append(f"tl.fromTo('{sel('intro')}', {{ opacity:0, y:16 }}, {{ opacity:1, y:0, duration:0.6, ease:'power2.out' }}, 0.3);")
js.append("tl.fromTo('#intro-t', { opacity:0, y:24, scale:0.96 }, { opacity:1, y:0, scale:1, duration:0.7, ease:'back.out(1.4)' }, 0.5);")
js.append("tl.fromTo('#intro-r', { width:0 }, { width:160, duration:0.6, ease:'power2.out' }, 0.95);")
js.append(f"tl.to('{sel('intro')}', {{ opacity:0, y:-10, duration:0.6, ease:'power2.in' }}, 4.3);")
js.append(f"tl.set('{sel('intro')}', {{ visibility:'hidden' }}, 4.9);")

# (caption-chunk timeline removed with the subtitle track)

# --- outro CTA ---
js.append("// outro CTA")
js.append(f"tl.set('{sel('cta')}', {{ visibility:'visible' }}, {q(cta_start)});")
js.append(f"tl.fromTo('{sel('cta')}', {{ opacity:0, y:16 }}, {{ opacity:1, y:0, duration:0.4, ease:'power2.out' }}, {q(cta_start)});")
js.append(f"tl.to('{sel('cta')}', {{ opacity:0, duration:0.45, ease:'power2.in' }}, {q(cta_end-0.45)});")
js.append(f"tl.set('{sel('cta')}', {{ visibility:'hidden' }}, {q(cta_end)});")

# --- full-bleed illustrative cutaways ---
js.append("// cutaway: 3am exhausted-parent illustration (Camille recap)")
js.append("tl.set('[data-card-id=\"cut-3am\"]', { visibility:'visible' }, 25.8);")
js.append("tl.fromTo('[data-card-id=\"cut-3am\"]', { opacity:0 }, { opacity:1, duration:0.4, ease:'power2.out' }, 25.8);")
js.append("tl.fromTo('#cz-3am', { scale:1.0 }, { scale:1.05, duration:4.3, ease:'sine.inOut' }, 25.8);")
js.append("tl.to('[data-card-id=\"cut-3am\"]', { opacity:0, duration:0.5, ease:'power2.in' }, 29.6);")
js.append("tl.set('[data-card-id=\"cut-3am\"]', { opacity:0, visibility:'hidden' }, 30.1);")

js.append("// cutaway: calm nursery photo (replaces the blurry shot 149-169)")
js.append("tl.set('[data-card-id=\"cut-scene\"]', { visibility:'visible' }, 149.04);")
js.append("tl.fromTo('[data-card-id=\"cut-scene\"]', { opacity:0 }, { opacity:1, duration:0.3, ease:'power1.out' }, 149.04);")
js.append("tl.fromTo('#cz-scene', { scale:1.0 }, { scale:1.05, duration:20.32, ease:'sine.inOut' }, 149.04);")
js.append("tl.to('[data-card-id=\"cut-scene\"]', { opacity:0, duration:0.3, ease:'power1.in' }, 169.06);")
js.append("tl.set('[data-card-id=\"cut-scene\"]', { opacity:0, visibility:'hidden' }, 169.36);")

js.append("// cutaway: co-regulation illustration (emotional ending)")
js.append("tl.set('[data-card-id=\"cut-coreg\"]', { visibility:'visible' }, 169.5);")
js.append("tl.fromTo('[data-card-id=\"cut-coreg\"]', { opacity:0 }, { opacity:1, duration:0.5, ease:'power2.out' }, 169.5);")
js.append("tl.fromTo('#cz-coreg', { scale:1.0 }, { scale:1.05, duration:7.0, ease:'sine.inOut' }, 169.5);")
js.append("tl.to('[data-card-id=\"cut-coreg\"]', { opacity:0, duration:0.5, ease:'power2.in' }, 176.0);")
js.append("tl.set('[data-card-id=\"cut-coreg\"]', { opacity:0, visibility:'hidden' }, 176.5);")

# --- motion-design beats ---
js.append("// M1 heart-rate / alarm chip")
js.append("tl.set('[data-card-id=\"mg-ecg\"]', { visibility:'visible' }, 14.4);")
js.append("tl.fromTo('[data-card-id=\"mg-ecg\"]', { opacity:0, y:-12 }, { opacity:1, y:0, duration:0.45, ease:'power3.out' }, 14.4);")
js.append("tl.set('#ecg-line', { strokeDasharray:700, strokeDashoffset:700 }, 14.4);")
js.append("tl.to('#ecg-line', { strokeDashoffset:0, duration:0.9, ease:'power1.inOut' }, 14.5);")
js.append("tl.to('#ecg-arrow', { scale:1.28, transformOrigin:'50% 50%', duration:0.45, ease:'sine.inOut', repeat:20, yoyo:true }, 15.0);")
js.append("tl.to('[data-card-id=\"mg-ecg\"]', { opacity:0, y:-10, duration:0.45, ease:'power2.in' }, 24.9);")
js.append("tl.set('[data-card-id=\"mg-ecg\"]', { opacity:0, visibility:'hidden' }, 25.4);")

js.append("// M2 stress-response trio")
js.append("tl.set('[data-card-id=\"mg-trio\"]', { visibility:'visible' }, 42.0);")
js.append("tl.set(['#trio-1','#trio-2','#trio-3'], { opacity:0 }, 42.0);")
js.append("tl.fromTo('[data-card-id=\"mg-trio\"]', { opacity:0, x:-20 }, { opacity:1, x:0, duration:0.4, ease:'power3.out' }, 42.0);")
js.append("tl.fromTo('#trio-1', { opacity:0, x:-14 }, { opacity:1, x:0, duration:0.35, ease:'power2.out' }, 42.25);")
js.append("tl.fromTo('#trio-2', { opacity:0, x:-14 }, { opacity:1, x:0, duration:0.35, ease:'power2.out' }, 42.75);")
js.append("tl.fromTo('#trio-3', { opacity:0, x:-14 }, { opacity:1, x:0, duration:0.35, ease:'power2.out' }, 43.25);")
js.append("tl.to('[data-card-id=\"mg-trio\"]', { opacity:0, x:-16, duration:0.45, ease:'power2.in' }, 49.9);")
js.append("tl.set('[data-card-id=\"mg-trio\"]', { opacity:0, visibility:'hidden' }, 50.4);")

js.append("// M3 circle of co-regulation")
js.append("tl.set('[data-card-id=\"mg-circ\"]', { visibility:'visible' }, 70.7);")
js.append("tl.fromTo('[data-card-id=\"mg-circ\"]', { opacity:0, scale:0.92, transformOrigin:'50% 50%' }, { opacity:1, scale:1, duration:0.5, ease:'back.out(1.4)' }, 70.7);")
js.append("tl.set('#circ-ring', { strokeDashoffset:848 }, 70.7);")
js.append("tl.to('#circ-ring', { strokeDashoffset:0, duration:1.0, ease:'power1.inOut' }, 70.9);")
js.append("tl.fromTo('#circ-dot', { opacity:0 }, { opacity:1, duration:0.3 }, 71.6);")
js.append("tl.to('#circ-dot', { rotation:360, svgOrigin:'210 210', duration:3.0, ease:'none', repeat:2 }, 71.6);")
js.append("tl.to('[data-card-id=\"mg-circ\"]', { opacity:0, scale:0.96, duration:0.45, ease:'power2.in' }, 76.5);")
js.append("tl.set('[data-card-id=\"mg-circ\"]', { opacity:0, visibility:'hidden' }, 77.0);")

js.append("// M4 breathing pacer")
js.append("tl.set('[data-card-id=\"mg-breathe\"]', { visibility:'visible' }, 112.6);")
js.append("tl.fromTo('[data-card-id=\"mg-breathe\"]', { opacity:0 }, { opacity:1, duration:0.6, ease:'power2.out' }, 112.6);")
js.append("tl.fromTo(['#breathe-c1','#breathe-c2'], { scale:0.72, svgOrigin:'180 180' }, { scale:1.0, duration:2.6, ease:'sine.inOut', repeat:2, yoyo:true }, 113.0);")
js.append("tl.to('[data-card-id=\"mg-breathe\"]', { opacity:0, duration:0.5, ease:'power2.in' }, 121.0);")
js.append("tl.set('[data-card-id=\"mg-breathe\"]', { opacity:0, visibility:'hidden' }, 121.6);")

js.append("// M5 three-step checklist")
js.append("tl.set('[data-card-id=\"mg-steps\"]', { visibility:'visible' }, 152.6);")
js.append("tl.set(['#step-1','#step-2','#step-3','#steps-res'], { opacity:0 }, 152.6);")
js.append("tl.set(['#check-1 .chk','#check-2 .chk','#check-3 .chk'], { strokeDasharray:40, strokeDashoffset:40 }, 152.6);")
js.append("tl.fromTo('[data-card-id=\"mg-steps\"]', { opacity:0, y:18 }, { opacity:1, y:0, duration:0.5, ease:'power3.out' }, 152.6);")
js.append("tl.fromTo('#step-1', { opacity:0, x:-12 }, { opacity:1, x:0, duration:0.35, ease:'power2.out' }, 152.9);")
js.append("tl.fromTo('#step-2', { opacity:0, x:-12 }, { opacity:1, x:0, duration:0.35, ease:'power2.out' }, 153.3);")
js.append("tl.fromTo('#step-3', { opacity:0, x:-12 }, { opacity:1, x:0, duration:0.35, ease:'power2.out' }, 153.7);")
js.append("tl.to('#check-1 .chk', { strokeDashoffset:0, duration:0.4, ease:'power2.out' }, 153.4);")
js.append("tl.to('#check-2 .chk', { strokeDashoffset:0, duration:0.4, ease:'power2.out' }, 156.1);")
js.append("tl.to('#check-3 .chk', { strokeDashoffset:0, duration:0.4, ease:'power2.out' }, 158.8);")
js.append("tl.fromTo('#steps-res', { opacity:0, scale:0.9, transformOrigin:'50% 50%' }, { opacity:1, scale:1, duration:0.5, ease:'back.out(1.6)' }, 164.8);")
js.append("tl.to('[data-card-id=\"mg-steps\"]', { opacity:0, y:-12, duration:0.5, ease:'power2.in' }, 166.5);")
js.append("tl.set('[data-card-id=\"mg-steps\"]', { opacity:0, visibility:'hidden' }, 167.0);")

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
print(f"Cues: {len(cues)} -> chunks: {len(chunks)} | shots: {len(CUTS)-1} | CTA: {cta_start}-{cta_end}s")
