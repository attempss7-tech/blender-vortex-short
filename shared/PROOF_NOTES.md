# 2D character proof — VALID (fixed 2026-11-12)

Technique: Grease Pencil (legacy GP v2, Blender 4.2) — one GP object per
body part, joint hierarchy under a root empty rotated 90° about X.
Module: `2d_rig.py` (import via importlib — filename starts with a digit;
see `build_proof.py` for the snippet). Proof scene:
`proof_2d_character.blend`, stills in `proof_stills/`.

## The upside-down bug (found + fixed 2026-11-12 by the restart coordinator)
The first proof rendered the character UPSIDE DOWN in every still (legs up,
head at the bottom edge). Root cause: the drawing's front normal is
placement-local -Y, so with no base rotation the character faced -Y (away
from a +Y camera). The code relied on the billboard Damped Track
(TRACK_NEGATIVE_Y) to close the 180° gap — but a 180° Damped Track is
degenerate and Blender took the PITCH flip (180° about X), inverting the
character while still facing the camera.
Fix (in `2d_rig.py`, backup of the broken version: `2d_rig.py.bak-broken`):
- `create_human` and `place()` now set the placement yaw to
  180° + facing_deg, so facing_deg=0 faces a +Y camera upright. The
  billboard Damped Track then only makes small corrections (no degeneracy).
- ALL front/back Z-offset signs flipped (after the yaw, root-local +Z
  points toward the camera): head +0.02, shoulders +0.03, elbows +0.01,
  hair/eyes/smile/cap/collar/buttons/hand/shoe positive; hip joints -0.03
  (thighs behind the torso). Without this flip the face details (eyes,
  smile) would hide behind the head fill and read as a faceless character.
- Docstring corrected: "L" = the character's own left (appears
  screen-right when facing the camera).

## Verified after the fix (stills viewed)
- f11 (1080p): upright flat 2D human mid-walk, face visible (eyes, smile,
  red cap), teal shirt with buttons + collar V, black stick limbs, brown
  shoes. Reads exactly like the @RicksClips3000 flat-2D style.
- f45: wave gesture — right arm raised out, reads clearly.
- billboard_side_f11: from the side camera the character still faces the
  camera upright (billboard re-pointing works).
- Walk cycle animates (limb poses differ across f01/f06/f11/f16/f31).

## Usage for the 4 video builders
- `create_human(name, location, height, skin, shirt, pants, hair, shoe,
  hat, facing_deg)` — facing_deg=0 faces a camera placed at +Y.
- Drivers: `walk_cycle`, `wave`, `point`, `head_turn`, `idle`,
  `settle_neutral`, `add_billboard(rig, camera)` (re-point per shot with
  `rig["billboard"].target = other_camera`), `place`.
- Do NOT "fix" the 180° base yaw back — it is the fix. Do NOT substitute
  3D figures. Worlds/scenery stay 3D meshes; HUMANS are always flat 2D.
