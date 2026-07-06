# CHECKLIST — EMO14_VID01_9X16

> Regle (voir instruction.md) : cocher chaque tache DES qu'elle est terminee,
> et ajouter les sous-taches decouvertes (une ligne par sequence des que
> sequences.json est rempli, retakes, corrections). Ne jamais lancer une
> generation sans lire cette liste, ni finir une etape sans la mettre a jour.

> Variante VERTICALE 9:16 (TikTok / Reels / Shorts) de EMO14_VID01.
> Script et decoupage identiques au projet horizontal (deja valides).
> Clips HeyGen regeneres en natif 1080x1920 ; b-roll : stills 9:16 regeneres
> depuis l'Element famille-jalousie puis re-animes (decision utilisateur 2026-07-06).

- [x] 1. Script valide place dans script.xlsx (copie de EMO14_VID01)
- [x] 2. sequences.json rempli depuis le script (19 sequences, orientation vertical)
- [x] 3. Clips HeyGen generes en 1080x1920 (19/19 -> heygen_clips/seqNN.mp4)
  - Retake global : v1 sans `fit` sortait letterboxee (bandes claires) ->
    regeneres en v2 avec `fit: cover` (2026-07-06). IDs dans heygen_video_ids.json.
  - [x] seq01 (emy)  - [x] seq03 (emy)  - [x] seq04 (emy)  - [x] seq06 (emy)
  - [x] seq10 (emy)  - [x] seq11 (emy)  - [x] seq14 (emy)  - [x] seq16 (emy)
  - [x] seq19 (emy)
  - [x] seq02 (broll, VO)  - [x] seq05 (broll, VO)  - [x] seq07 (broll, VO)
  - [x] seq08 (broll, VO)  - [x] seq09 (broll, VO)  - [x] seq12 (broll, VO)
  - [x] seq13 (broll, VO)  - [x] seq15 (broll, VO)  - [x] seq17 (broll, VO)
  - [x] seq18 (broll, VO)
- [x] 4. Clips HeyGen relus (contact sheet: review_frames/heygen_contact.png) — valides par l'utilisateur 2026-07-06
- [x] 5. Element famille-jalousie reutilise (e9283b1e..., cree dans EMO14_VID01)
- [x] 6. Stills 9:16 generes depuis l'Element (10/10, nano_banana_flash ~1.5cr/still) — valides par l'utilisateur 2026-07-06
  - Note : seedream_v5_lite (1cr) teste d'abord mais son filtre nsfw bloque toute scene avec enfants -> nano_banana_flash.
  - Contact sheet : review_frames/stills_contact.png
  - [x] s02  - [x] s05  - [x] s07  - [x] s08  - [x] s09
  - [x] s12  - [x] s13  - [x] s15  - [x] s17  - [x] s18
- [x] 7. B-roll animes (10/10, seedance_2_0 fast 720p, ~3.5cr/s) — valides par l'utilisateur 2026-07-06
  - Toutes les durees couvrent la VO HeyGen (verifie). Contact sheet : review_frames/broll_contact.png
  - [x] broll02  - [x] broll05  - [x] broll07  - [x] broll08  - [x] broll09
  - [x] broll12  - [x] broll13  - [x] broll15  - [x] broll17  - [x] broll18
- [x] 8. Base assemblee : python studio.py build EMO14_VID01_9X16 (119.52s, 19/19 segments a la duree cible)
- [x] 9. Base relue (contact sheet : review_frames/base_timeline.png ; audio VO verifie) — validee par l'utilisateur 2026-07-06
- [x] 10. Motion graphics dans public/index.html adaptes au format vertical (17 beats repris de EMO14_VID01,
      retimes sur les nouvelles frontieres, repositionnes 1080x1920 hors zone UI TikTok/Reels ;
      card-11 « tire des deux cotes » restructuree en colonne verticale ; lint OK ;
      captures : review_frames/overlays_contact.png + ov_cNN.png) — valide par l'utilisateur 2026-07-06
- [x] 11. Rendu final : python studio.py render EMO14_VID01_9X16 (119.48s)
  - Fix 1 : input-video.mp4 re-encode avec keyframes denses (-g 25) — le GOP long faisait geler les seeks.
  - Fix 2 : rendu avec HYPERFRAMES_EXTRACT_CACHE_DIR=off — le cache d'extraction sur C: echoue en
    symlink EPERM vers le projet sur D: (Windows sans mode developpeur).
- [x] 12. QA finale OK (1080x1920 25fps h264 + aac 48k stereo ; frames cles review_frames/final_qa.png ;
      audio verifie debut/fin) — livrable : final/EMO14_VID01_9X16.mp4 (182 Mo).
      NB : studio.py status affiche « render » comme prochaine etape car il cherche output/<CODE>.mp4 ;
      le final a ete deplace dans final/ conformement a instruction.md.
      Reste : validation finale utilisateur (checkpoint 7) -> TERMINE
