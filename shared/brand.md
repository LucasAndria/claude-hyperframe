# Charte graphique — vidéos EMO (La Petite Crèche)

Référence unique pour toutes les compositions HyperFrames. Les assets de ce
dossier (`shared/`) sont copiés automatiquement dans chaque nouveau projet par
`python studio.py new`.

## Palette

| Rôle | Hex | Usage |
|---|---|---|
| Crème (`--cream`) | `#fbf6ef` | fonds de cartes, texte clair sur scrim |
| Terracotta (`--accent`) | `#d98b63` | accents, mots-clés, soulignés |
| Beige doux (`--muted`) | `#d8cabb` | texte secondaire, filets |
| Encre (`--ink`) | `#271c16` | texte principal sur fond clair |

## Typographie

- **Montserrat** (`shared/fonts/Montserrat.ttf`) pour tout le texte à l'écran.
- Titres : graisse 600–700 ; texte courant : 400–500.

## Style des overlays

- La vidéo reste **plein cadre** en permanence ; les overlays ne la recouvrent jamais entièrement.
- ~8 beats typographiques sobres par vidéo de 2 min : fondus doux, scrims légers pour la lisibilité.
- Mouvements retenus via la librairie `shared/motion/` (`window.RefMotion`) —
  intensité globale réglable dans `shared/motion/motion.config.json` (défaut 0.65).

## Contenu de `shared/`

- `motion/` — librairie de motion design déterministe (+ exemple dans `motion/example/`)
- `fonts/Montserrat.ttf` — police de la marque
- `vendor/gsap.min.js` — GSAP pour les animations
- `motion-example/` — rendu d'exemple de la librairie motion
