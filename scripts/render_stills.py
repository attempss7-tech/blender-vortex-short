# render_stills.py — validation stills from scenes/vortex.blend
# (or scenes/proof.blend with --blend).
#
# Usage (from ~/workspace/blender_chicken):
#   blender --background --python scripts/render_stills.py -- \
#       --engine workbench --frames 100,310,400,600,720,820,900,1000,1060,1200 \
#       --out out/stills/proof --res 540
#
# --engine workbench: fast geometry/framing check (flat shading).
# --engine cycles:    colour/material check (CPU, 16 samples + denoise).
# The camera for each frame is picked from the timeline markers (the
# marker at or before the frame whose camera is bound), so stills use
# exactly the shot camera that frame renders with.
import argparse
import os
import sys
import time

import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--engine", default="workbench",
                choices=["workbench", "cycles"])
ap.add_argument("--frames", default="100,310,400,600,720,820,900,1000,1060,1200")
ap.add_argument("--out", default="out/stills/all")
ap.add_argument("--res", type=int, default=540)
ap.add_argument("--samples", type=int, default=16)
ap.add_argument("--blend", default="scenes/vortex.blend")
args = ap.parse_args(argv)

here = os.path.dirname(os.path.abspath(__file__))
proj = os.path.normpath(os.path.join(here, ".."))
blend = args.blend if os.path.isabs(args.blend) else os.path.join(
    proj, args.blend)
outdir = args.out if os.path.isabs(args.out) else os.path.join(proj, args.out)
os.makedirs(outdir, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=blend)
scene = bpy.context.scene
scene.render.resolution_x = args.res
scene.render.resolution_y = args.res * 16 // 9
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"

if args.engine == "workbench":
    scene.render.engine = "BLENDER_WORKBENCH"
    sh = scene.display.shading
    sh.light = "STUDIO"
    sh.color_type = "MATERIAL"
    try:
        sh.show_shadows = True
    except AttributeError:
        pass
else:
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = args.samples
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = "OPENIMAGEDENOISE"

markers = sorted(((m.frame, m.camera) for m in scene.timeline_markers
                  if m.camera is not None))


def camera_for(frame):
    cam = None
    for mf, mc in markers:
        if mf <= frame:
            cam = mc
        else:
            break
    return cam or scene.camera


for f in [int(x) for x in args.frames.split(",") if x.strip()]:
    t0 = time.time()
    scene.frame_set(f)
    scene.camera = camera_for(f)
    scene.render.filepath = os.path.join(
        outdir, "f%04d_%s.png" % (f, args.engine))
    bpy.ops.render.render(write_still=True)
    print("STILL f%d %s cam=%s in %.1fs -> %s"
          % (f, args.engine, scene.camera.name, time.time() - t0,
             scene.render.filepath))
print("DONE", args.engine)
