# Guide — produire une vidéo EMO de A à Z

Ce guide s'adresse à toute l'équipe, aucune connaissance technique requise.
Tout se passe dans **Claude Code** (ouvrir ce dossier, taper les phrases en
gras) et avec **une seule commande** : `python studio.py`.

À tout moment, pour savoir où en est chaque vidéo et quelle est la prochaine
étape :

```
python studio.py status
```

---

## Étape 1 — Créer le projet

```
python studio.py new EMO15_VID01 --script "chemin/vers/EMO15_VID01.xlsx"
```

Cela crée le dossier `projects/EMO15_VID01/` avec tout dedans : le script, la
config (avatar Emy + voix française Audrey, 16:9, 25 img/s), et les assets de
la marque déjà en place. Ajouter `--vertical` pour un format 9:16
(Reels/TikTok). **Aucun autre projet n'est touché.**

## Étape 2 — Préparer les séquences

Dans Claude Code, demander :

> **Remplis sequences.json pour EMO15_VID01 à partir de son script.xlsx**

Claude lit le script Excel et structure chaque séquence (Emy face caméra ou
b-roll illustré).

## Étape 3 — Générer les clips Emy (HeyGen)

> **Génère les clips HeyGen pour EMO15_VID01**

Un clip par séquence arrive dans `projects/EMO15_VID01/heygen_clips/`.
Si Claude dit qu'un outil HeyGen manque : taper `/mcp` pour reconnecter, puis
redemander.

## Étape 4 — Générer les b-roll (Higgsfield)

> **Génère les b-roll Higgsfield pour EMO15_VID01**

Claude crée une famille visuelle cohérente puis anime chaque plan. Les clips
arrivent dans `projects/EMO15_VID01/higgsfield/clips/`.

## Étape 5 — Assembler la vidéo de base

```
python studio.py build EMO15_VID01
```

(ou demander : **Assemble la base de EMO15_VID01**). Résultat :
`projects/EMO15_VID01/output/EMO15_VID01_1_base.mp4` — la vidéo montée, sans
habillage.

## Étape 6 — Créer les habillages typographiques

> **Crée les overlays HyperFrames pour EMO15_VID01** (style sobre, charte dans shared/brand.md)

Claude compose l'habillage (mots-clés, titres, fondus) dans
`projects/EMO15_VID01/public/index.html` et le fait valider avec des captures.

## Étape 7 — Rendu final

```
python studio.py render EMO15_VID01
```

La vidéo finale est là : **`projects/EMO15_VID01/output/EMO15_VID01.mp4`** 🎉

---

## En cas de problème

| Symptôme | Solution |
|---|---|
| Un outil HeyGen/Higgsfield « n'existe pas » | `/mcp` pour reconnecter, puis redemander |
| Le rendu HyperFrames échoue | `npx hyperframes doctor` |
| `ffmpeg introuvable` | installer ffmpeg et l'ajouter au PATH |
| Je ne sais plus où j'en suis | `python studio.py status` |

Chaque projet est **autonome** dans `projects/<CODE>/` : script, config, clips,
habillage et résultats. On peut travailler sur plusieurs vidéos en parallèle
sans jamais rien écraser.
