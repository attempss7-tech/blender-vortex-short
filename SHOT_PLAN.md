# SHOT PLAN — V1 "The Accidental Flaw That Saved Airliners" (vortex generators)

Voice: Warm Pebble, 42.768 s, 1284 frames (0–1283) @30 fps. All frame ranges
from `voice/words.json` (vosk, hand-fixed). Hard cuts at shot boundaries;
every shot has camera movement. No text/captions baked in anywhere.
2D humans: flat Grease Pencil rigs from `../shared/2d_rig.py` (Eng1, Eng2).
Worlds/planes/airflow: own-built 3D meshes, no downloaded models.

Sets (separate world locations so cameras never see another set):
- Hangar set at origin (floor, back wall, workbench, wing on trestles,
  calendar board). S1.
- Airfield set at x=+60 (runway strip, windsock, hangar silhouette). S2.
- Wing-lab set at x=-60, z=20 (one big wing section + airflow rigs). S3/S6/S7/S9.
- Sky sets: hero jet + smooth jets fly at y=-40..+40, z=18–30 (S2/S5/S8);
  airliner at x=+60, z=26 (S10). Clouds scattered near each sky set.

## S1 — f0–215 (0–7.17 s) — Hangar: sanding the defect, then the realization
Words: "Engineers spent two years trying to smooth out this wing defect —
until they realized it was keeping planes in the air." (f9–196)
- f9–111: Eng1 SANDS the wing on trestles — right arm sawing back and forth
  (shoulder oscillation ~2 strokes/s), sanding dust puffs drifting off the
  wing edge; the defect patch on the wing GLOWS red/pulses, then fades as
  the wing is smoothed. Calendar pages FLIP twice (f30, f70) = time passing.
  Eng2 stands by, idle + head turn toward the wing.
- f119–147: "realized" — both engineers STOP, look up together (head tilt
  up), Eng2 POINTS up at the model plane.
- f153–196: the small model plane on the bench LIFTS OFF, rises and banks
  gently = "keeping planes in the air".
- Camera: slow dolly-in toward the wing (f0–111), then tilt up following
  the model plane (f119–215). Focus shifts wing → plane.
- Test frame: f100 (sanding + glowing defect), f170 (plane lifting).

## S2 — f216–353 (7.2–11.77 s) — 1940s airfield: the prototypes stall
Words: "Back in the late 1940s, early jet prototypes kept stalling at
low speeds." (f216–343)
- f216–296: three early jets taxi down the runway and lift off, climbing
  shallowly; hero jet (middle) pitches up progressively from f278.
- f303–318 ("stalling"): hero jet SHUDDERS (rapid small pitch/roll jitter),
  nose drops, and the jet DROPS ~4 m, recovering low. The other two wobble.
- f318–353: hero jet flies on low and unsteady, slight porpoising.
- Camera: tracking shot alongside the runway, panning with the hero jet,
  slight push-in through the stall.
- Test frame: f310 (mid-shudder/drop).

## S3 — f354–499 (11.8–16.63 s) — Wing close-up: airflow breaks away, lift dies
Words: "The airflow over the smooth metal broke away too easily, instantly
killing lift." (f354–487)
- f354–404: five airflow lines stream smoothly over the wing (flowing
  dashes: small chevron markers travel along each line).
- f360–414 ("airflow… broke away"): the lines PEEL OFF — each line pivots
  up off the wing surface in sequence (front to back), tails lifting away.
- f450–476 ("instantly killing"): the big green LIFT arrow above the wing
  shrinks and VANISHES; the wing section starts to SINK.
- f476–499 ("lift"): wing sinks ~2 m, airflow lines stream off into the
  distance, detached.
- Camera: slow push-in on the wing section, slight lateral drift.
- Test frame: f400 (lines peeling), f480 (arrow gone, sinking).

## S4 — f500–669 (16.67–22.3 s) — The battered plane: burrs pop up
Words: "But on one battered test plane, tiny metal burrs were accidentally
sticking up along the wing edge." (f500–658)
- f500–556: camera tracks along the battered hero jet's wing edge (dents,
  patches, scuffed paint). No engineer here — v1 stills showed a person
  at this macro distance would sit behind the camera or fill the frame;
  the burrs popping carry the shot alone.
- f556–658: burrs POP UP one by one along the leading edge — staggered
  2-frame pops, the burst centred on "burrs" (f576–587), continuing
  "along the wing edge" (f629–658) as the camera glides past them.
- Camera: tracking glide along the wing edge, close.
- Test frame: f600 (burrs popping, engineer pointing).

## S5 — f670–777 (22.33–25.9 s) — The battered prototype flies better
Words: "Counterintuitively, that prototype flew better than the rest."
(f670–765)
- f670–777: hero jet (burrs visible on its wings) flies STEADY and level
  past the camera; the two smooth jets beside/behind it WOBBLE — pitching
  and rolling, one porpoising, one wallowing side to side.
- Camera: side tracking shot, slight push-in on the hero jet.
- Test frame: f720 (steady hero vs wobbling others).

## S6 — f778–874 (25.93–29.13 s) — Bumps force air down onto the wing
Words: "Those bumps forced high-energy air down onto the surface."
(f778–868)
- f778–806: airflow lines approach HIGH above the wing, angled up.
- f786–844 ("bumps forced high-energy air down"): the lines BEND DOWN —
  each line pivots down onto the wing surface in sequence, hugging it.
- f844–874: lines stream flat along the surface, pressed down behind the
  row of small fin-bumps; the bumps are clearly visible.
- Camera: low-angle push-in on the wing, focus on the bump row.
- Test frame: f820 (lines bending down onto the surface).

## S7 — f875–970 (29.17–32.33 s) — Micro-vortices glue the airflow on
Words: "creating micro-vortices that glued the airflow to the wing"
(f875–969)
- f875–889: airflow lines stream over the wing, loose.
- f889–917 ("micro-vortices"): five small spiral vortices APPEAR above the
  wing (scale in) and SPIN fast (helix tubes rotating about the airflow
  axis), one behind each bump.
- f922–969 ("glued the airflow to the wing"): the airflow lines SNAP back
  down onto the wing surface and STICK — flat, tight to the surface,
  tracking the vortices.
- Camera: slow dolly along the wing span.
- Test frame: f900 (vortices spinning), f940 (airflow glued).

## S8 — f971–1031 (32.37–34.37 s) — Steep climb, airflow still glued
Words: "even during steep climbs" (f971–1016)
- f971–990: hero jet levels, then pitches up HARD.
- f990–1016 ("steep climbs"): jet climbs at ~50° through the clouds,
  airflow lines visibly GLUED along its wings (flat, attached), vortices
  spinning at the wing roots; the jet RISES ~10 m across the shot.
- Camera: low-angle tracking shot tilting up with the climb.
- Test frame: f1000 (steep climb, glued airflow).

## S9 — f1032–1099 (34.4–36.63 s) — The name moment: vortex generators
Words: "Today, they're called vortex generators." (f1032–1089)
- f1032–1053: close-up glide along the wing; the fin row comes into view.
- f1053–1089 ("vortex generators"): the little fins catch the light in
  sequence — a highlight sweep travels down the row (each fin briefly
  brightens as the sweep passes), camera gliding past them in macro.
- No text on screen — the fins themselves are the subject.
- Camera: macro glide along the fin row, shallow feel via close framing.
- Test frame: f1060 (fin row close-up, highlight sweep).

## S10 — f1100–1283 (36.67–42.77 s) — The modern airliner
Words: "And almost every modern airliner flies with hundreds of engineered
flaws purposely glued to its wings." (f1100–1276)
- f1100–1165: modern airliner flies in, smooth and level; camera closes on
  the wing — ROWS of tiny fins visible along both wings.
- f1165–1240: slow pull-back reveals the whole airliner gliding through
  clouds, fins still visible on the wings; gentle banking turn.
- f1240–1283: wide hero shot, airliner flying smooth into the distance;
  fade-out happens in assembly (ffmpeg, from 42.268 s) — never after the
  voice. Last word "wings" ends f1276; video ends f1283.
- Camera: push-in then slow pull-back + slight orbit.
- Test frame: f1200 (airliner + fin rows).

## Notebook test frames (one per shot)
100, 310, 400, 600, 720, 820, 900, 1000, 1060, 1200
