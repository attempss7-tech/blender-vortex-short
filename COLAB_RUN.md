# Running the V1 vortex short on Colab

The project is built and validated locally. The Colab GPU does the Eevee
render only. The notebook is `notebook/vortex_colab.ipynb`.

## Click-path

1. Open https://colab.research.google.com.
2. **File > Open notebook > GitHub tab** — paste
   `attempss7-tech/blender-vortex-short`, open
   `notebook/vortex_colab.ipynb`. (Or upload the `.ipynb` file
   directly: File > Upload notebook.)
3. **Runtime > Change runtime type > T4 GPU > Save.** The notebook fails
   fast with a clear message if no GPU is attached — do not render on CPU
   (Eevee falls back to software rendering, far too slow).
4. Run the cells **top to bottom, in order**. Do not use "Run all" blindly:
   you must STOP after the Eevee test-frames cell and inspect the 10 frames
   before running any shard cell.
5. The first cell mounts Google Drive — click through the auth prompt.
   Frames go to `MyDrive/vortex_short/frames/`, test frames to
   `MyDrive/vortex_short/test_frames/`, the final video to
   `MyDrive/vortex_short/final/`.

## The mandatory stop: Eevee test frames

**EGL fix (proven 2026-11-12 on the chicken short, baked into the install
cell):** Colab ships the NVIDIA EGL library
(`/usr/lib64-nvidia/libEGL_nvidia.so.0`) but no vendor file for it, so
Blender's EGL context fails (`EGL_BAD_MATCH`) and Eevee silently falls back
to CPU rendering at ~5 min/frame. The install cell writes
`/usr/share/glvnd/egl_vendor.d/10_nvidia.json` before any render; with it,
Eevee uses the T4 at ~1.5–3.5 s/frame. The vendor file lives only in the
live session — after a session drop, re-running the install cell
re-creates it. If a render ever runs at minutes-per-frame, the vendor
file is missing: stop, re-run the install cell, re-run the render.

Eevee was never validated locally (no GPU there). The test-frames cell
renders 10 frames, one per shot, and displays them inline. Check every one:

- f100: both engineers upright, flat 2D, facing the camera (NOT upside
  down); red defect patch on the wing; hangar warm, not black.
- f310: hero jet nose-high over the runway (the stall), fully in frame.
- f400: airflow lines peeling off the wing. f600: burrs on the wing edge.
- f720: hero jet steady, two smooth jets wobbling behind it.
- f820: airflow lines bent down onto the wing. f900: vortices spiralling.
- f1000: steep climb, whole jet in frame. f1060: fin row + gleam sweep.
- f1200: airliner with fin rows visible on its wings.
- No black/missing objects anywhere; sky blue in the outdoor shots.

**If the 2D engineers are missing or upside down:** run the FIX cell
below (diagnostic + re-render of f100) and report the output — do not
continue to the shards. **If all 10 frames look right:** skip the fix
cell and run the 3 shard cells.

## Shards (frames 0–1283 in 3 × 428)

- Shard 1: 0–427 · Shard 2: 428–855 · Shard 3: 856–1283.
- Each shard renders in 4 batches of 107 frames and copies each batch to
  Drive immediately. Per-frame timings print as it goes; each shard ends
  with a count check against Drive.
- Expected speed is unmeasured until the first test frame — budget roughly
  1.5–3.5 s/frame on a T4 (10–25 min per shard) and re-estimate from the
  test-frames timings.

## If a session drops mid-shard

Colab sessions reset/disconnect (12 h cap, ~90 min idle, GPU preemption).
Nothing is lost beyond the in-progress batch (~5 min of rendering):

1. Reopen the notebook (same file, same account).
2. Re-run the setup cells in order: mount Drive + GPU check, install
   Blender + libs, clone repo (or pull).
3. Re-run the interrupted shard cell. It first syncs that shard's finished
   frames from Drive back to local disk, then renders only the missing
   frames, batch by batch.
4. Continue with the remaining shard cells, then assembly.

Do NOT re-run the test-frames cell unless you changed something — the test
frames are already on Drive.

## Assembly + verification

The assembly cell checks all 1,284 frames are on Drive (and stops, listing
any missing frames, if not), then runs ffmpeg: PNG sequence → h264 mp4
(crf 17), fade-in 0.5 s + fade-out 0.5 s from 42.268 s (inside the voice,
never after it), muxed with the sound mix (`assets/mix.wav`, already
−14.6 LUFS). The verification cell prints ffprobe details + an ebur128
loudness reading.

Expected final: `vortex_short.mp4`, ~42.77 s, 1080x1920, 30 fps,
h264 + AAC, ~−14.6 LUFS.

## If the committed .blend fails

The last markdown cell has the rebuild command: it re-runs
`scripts/build_all.py` in Colab (~10 s) to regenerate
`scenes/vortex.blend` from the scripts, then re-run the
test-frames cell.

## Known limits (from BUILD_NOTES.md)

- Workbench stills don't show the world background; the blue sky / warm
  hangar only appear in Eevee — the test frames are the real check.
- S8's glued flow lines + vortices are small at 27 m; the climb is the
  read there.
- The airliner window strip is a solid dark band (stylization).
- No captions/text are baked in — captions are a separate overlay step.
