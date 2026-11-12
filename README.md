# V1 — "The Accidental Flaw That Saved Airliners" (Blender short)

A 42.8 s vertical explainer short for @ExplainerMaan: how tiny accidental
burrs on a 1940s jet prototype became the vortex generators on every
modern airliner. Built in Blender 4.2.23 (Eevee, 1080x1920, 30 fps,
frames 0–1283) with scripted geometry — no downloaded models, no GUI
modelling. Humans are flat 2D Grease Pencil characters
(@RicksClips3000 style); planes, wings, airflow and sets are own-built 3D.

## Layout

- `scripts/build_all.py` — master build; regenerates `scenes/vortex.blend`
- `scripts/common.py`, `scripts/props.py`, `scripts/shots.py` — helpers,
  object builders, the 10 shots' animation
- `scripts/colab_render.py` — frame-range render driver (used by Colab)
- `scripts/render_stills.py` — Workbench validation stills
- `scripts/make_mix.py` — sound mix (voice + original pad score + SFX)
- `shared/2d_rig.py` — the flat 2D human rig (copy of the proven shared rig)
- `scenes/vortex.blend` — the built scene (reproducible from scripts)
- `assets/` — `words.json` (voice timings), `mix.wav` (−14.6 LUFS),
  `cues.md`
- `notebook/vortex_colab.ipynb` — Colab GPU render notebook
- `SHOT_PLAN.md` — phrase-by-phrase shot plan (every phrase → animated action)
- `COLAB_RUN.md` — click-path for the Colab render
- `BUILD_NOTES.md` — per-phrase verdicts, decisions, known limits

## Rebuild locally

```
/path/to/blender-4.2.23 --background --python scripts/build_all.py
```

## Render on Colab

See `COLAB_RUN.md`. Short version: open the notebook from this repo in
Colab with a T4 GPU, run the cells in order, STOP and inspect the 10 Eevee
test frames, then run the 3 shard cells (0–427, 428–855, 856–1283) and
assembly. Fade-out sits inside the final 0.5 s of the voice (from
42.268 s) — never after it.
