# BUILD NOTES — V1 "The Accidental Flaw That Saved Airliners"

Blender 4.2.23, Eevee, 1080x1920, 30 fps, frames 0–1283 (42.768 s).
Voice: Warm Pebble (avocado_v2:chip, speed 112), 42.768 s, 116 words.
Built 2026-11-12. Repo: `attempss7-tech/blender-vortex-short`.

## Build

- `scripts/build_all.py` builds everything from scripts in ~5–11 s:
  408 objects (237 meshes, 21 Grease Pencil, 34 curves), 11,920 polys,
  133 actions, 10 marker-bound cameras.
- Rebuild-from-scratch check: identical stats and identical byte size
  (4,712,984 bytes) across rebuilds. The .blend MD5 differs between
  rebuilds (Blender write-order nondeterminism) — stats + size are the
  reproducibility criterion, and both match.
- The 2D rig lives in the repo at `shared/2d_rig.py` (copy of the proven
  shared rig) and both `build_all.py` and `shots.py` find it via a
  `_find_rig()` resolver: repo layout (`scripts/../shared`) first, then
  the workspace layout (`scripts/../../shared`). The Colab rebuild path
  was proven by building from a repo-layout copy in /tmp — identical
  stats (408 objects / 11,920 polys / 133 actions / 10 cameras).
- GitHub commit `7b62eef8` (2026-11-12): 18 files pushed, tree verified
  via the API (README, 7 scripts, shared rig + proof notes, words.json,
  mix.wav, cues.md, .blend, notebook, 3 docs).
- Layout: `scripts/` (common, props, shots, build_all, render_stills,
  colab_render, make_mix), `scenes/vortex.blend`, `assets/` (words.json,
  mix.wav, cues.md, stems), `notebook/vortex_colab.ipynb`,
  `SHOT_PLAN.md`, `COLAB_RUN.md`, `out/stills/` (Workbench validation).
- Sound mix: `assets/mix.wav` — voice (gain only) + original 8-chord
  ambient pad (C-G-Am-F-C-G-F-G, ducked −3 dB under speech, bed −10 LU
  vs voice) + synthesized SFX (wind swells at the stall/peel/climb,
  10 metallic burr ticks, chime at "vortex generators", jet rumble
  under sky shots). Verified: −14.6 LUFS integrated (ffmpeg ebur128),
  −1.20 dBTP, exactly 42.768 s, 48 kHz stereo 24-bit. Stems kept
  locally (`stem_voice/music/sfx.wav`); only mix.wav + words.json +
  cues.md are pushed to the repo. Two bugs found while building the mix:
  `widen()` in dsp.py takes MONO — passing stereo made np.pad allocate
  ~8.7 GB and OOM-killed the run (fix: widen the mono bed, it returns
  stereo); and the last rumble span ended at 42.77 s, past N — clamp
  span ends to N (fix in make_mix.py).

## Per-phrase verdicts (Workbench stills viewed, v4)

Stills viewed (540x960, `out/stills/v3/` + `out/stills/v4/`):
f60, f130, f180 (S1); f250, f310, f345 (S2); f370, f400, f480 (S3);
f520, f600, f650 (S4); f720 (S5); f800, f860 (S6); f900, f950 (S7);
f1000 (S8); f1060 (S9); f1150, f1220, f1280 (S10).

- S1 "two years trying to smooth out this wing defect" — PASS. Both 2D
  engineers upright, flat, faces visible; Eng1's arm saws at the wing
  (f60), red defect patch pulses then vanishes by f111, calendar pages
  flip (f28, f68). "Realized… keeping planes in the air" — PASS: both
  look up, Eng2 points up (f130), model plane lifts off the bench and
  banks (f180).
- S2 "kept stalling at low speeds" — PASS. Hero jet pitches up steeply
  and shudders at f303–318 (f310 still: nose-high ~40° over the runway),
  drops, recovers low (f345). Smooth jets wobble behind on the far side.
- S3 "airflow… broke away… killing lift" — PASS. Lines stream flat
  (f370), peel off in sequence (f400), lift arrow vanishes f450–476 and
  the wing sinks (f480).
- S4 "tiny metal burrs… sticking up along the wing edge" — PASS. Burrs
  pop one by one along the near wing edge (f600: 3 visible mid-pop,
  f650: row near the root), camera gliding along the edge.
- S5 "that prototype flew better than the rest" — PASS. Hero steady and
  level (burrs visible on its wing), both smooth jets wobbling behind
  it (f720).
- S6 "bumps forced high-energy air down onto the surface" — PASS. Lines
  start high, bend down in sequence (f800), hug the surface by f860;
  fin-bumps visible on the wing.
- S7 "micro-vortices that glued the airflow to the wing" — PASS. Pale
  cyan spiral vortices appear and spin (f900), airflow snaps flat onto
  the wing and sticks (f950).
- S8 "even during steep climbs" — PASS. Jet climbs at ~49° through the
  clouds (f1000), glued flow lines + vortices visible on its wings.
- S9 "they're called vortex generators" — PASS. Fin row in close-up with
  the highlight gleam sweeping along it (f1060). No text on screen.
- S10 "almost every modern airliner flies with hundreds of engineered
  flaws" — PASS. Fin rows visible on the wings in the close-up (f1150),
  slow pull-back to the whole airliner gliding through clouds (f1280).
  Last word "wings" ends f1276; video ends f1283; fade-out sits inside
  the final 0.5 s (assembly fades from 42.268 s) — no dead silence.

## Decisions (from the stills iterations v1→v4)

- **FOV correction (the big one).** With `sensor_fit="VERTICAL"` the
  vertical FOV uses the 24 mm sensor HEIGHT, not the 36 mm width:
  horizontal half-FOV at 36 mm is only ~10.7°, not 15.5°. The v1
  cameras were all ~1.5x too close (jets filled the frame, Eng2 out of
  frame). All flight cameras were re-placed from the correct formula
  (28 mm at ~27 m for the 8 m jets, 26 mm for the S5 formation, 30 mm
  for the climb, 47 m pull-back for the 18 m airliner finale).
  Documented in `scripts/common.py` so the next videos don't repeat it.
- **S1 restaged.** Wing shrunk 6 m → 5 m span; engineers moved closer
  together (x −1.4/+1.1) and forward of the wing (y ≥ 1.6) so the wing
  slab never cuts across them; calendar moved onto the door (x=−2.0)
  so it sits inside the narrow frame.
- **S4 has no engineer.** v1 showed a person at the wing-macro distance
  would sit behind the camera or fill the frame; the burrs popping
  carry the shot alone. Eng2 appears in S1 only.
- **All 10 burrs on the near wing.** v3 put 5 on the far wing, where
  S4's camera could never see them pop. Now y_s −3.2..+0.4 (camera
  side), pops staggered f556–646.
- **Clouds moved out of sightlines.** CloudA (−75,12,13) no longer sits
  under the wing-lab wing; CloudE (55,18,18) no longer fills the S5
  foreground; CloudB moved away from the S3 camera position.
- **S9 gleam tracks the focus.** v2 swept the full fin row and outran
  the frame; now it travels with the camera's focus point (local
  +1.2 → −1.4) during the name moment.
- **Characters face the camera via keyframed yaw** (`face_camera` in
  common.py), not the rig's billboard constraint — a Damped Track
  target can't be keyframed per shot, and keyframed yaw is
  deterministic. The 180° base yaw fix in `2d_rig.py` was left alone.
- **No Outline material in this project** (no inverted-hull outlines),
  so the chicken project's black-shell failure mode doesn't apply;
  the notebook's fix cell is a GP/diagnostic + re-render cell instead.

## Timings (measured)

- build_all.py: ~5–11 s. Workbench stills: ~1–1.7 s each at 540x960.
- make_mix.py: ~21 s. Colab Eevee estimate: unmeasured until the first
  test frame; budget ~1.5–3.5 s/frame on a T4 (chicken measured ~3.5).

## Known limits

- Workbench stills don't show the world background (dark grey backdrop
  in stills); the blue sky / warm hangar only appear in Eevee — the
  Colab test frames are the real lighting check.
- The hangar floor shows long streak shadows in Workbench (studio-light
  artifact); Eevee sun shadows will differ — check the f100 test frame.
- S8's glued flow lines + vortices are small at 27 m (thin blue
  squiggles on the wing) — the climb itself is the read there.
- The airliner window strip is a solid dark band, not individual
  windows (stylization, reads fine at render distance).
- S9's fins read as flat slabs from the front — the row + gleam +
  pulses carry the "name moment", not fin detail.
- The model plane's S8 flow rig and the smooth jets' S8 rigs exist but
  are permanently hidden (scale 0.001) — dead weight, ~negligible.

## Colab watch-list (for the test-frames stop)

- f100: both engineers upright, flat 2D, facing camera (NOT upside
  down); defect patch red on the wing; hangar warm, not black.
- f310: hero jet nose-high over the runway, not cropped.
- f400/f480: airflow lines peeling / lift arrow gone.
- f600: burrs on the wing edge. f900: vortices spiralling. f1000: steep
  climb, whole jet in frame. f1060: fin row + gleam. f1200: airliner
  with fin rows on the wings.
- GP characters must render in Eevee (they do in Workbench; Eevee GP
  support is standard, but this is the first Eevee check for this rig).
