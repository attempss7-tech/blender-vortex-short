# build_all.py — master build for the V1 vortex-generators Blender short.
#
# Builds all 10 shots in ONE scene on ONE 1284-frame timeline, with the
# sets built once and shared, 10 marker-bound cameras, hangar/day lighting
# keyframed per shot, and a central visibility schedule (see
# schedule_visibility). Saves scenes/vortex.blend (BLENDER_EEVEE_NEXT,
# 1080x1920, 30 fps, frames 0-1283).
#
# Run from ~/workspace/blender_shorts_4/v1_vortex:
#   /home/hatch/workspace/blender_chicken/tools/blender-4.2.23-linux-x64/blender \
#       --background --python scripts/build_all.py
import importlib.util
import os
import sys
import time

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import common as cm  # noqa: E402
import props  # noqa: E402
import shots  # noqa: E402

def _find_rig():
    """Locate 2d_rig.py: repo layout (scripts/../shared) first, then the
    workspace layout (scripts/../../shared), then next to this file."""
    here = os.path.dirname(os.path.abspath(__file__))
    for cand in (os.path.join(here, "..", "shared", "2d_rig.py"),
                 os.path.join(here, "..", "..", "shared", "2d_rig.py"),
                 os.path.join(here, "2d_rig.py")):
        if os.path.exists(cand):
            return os.path.normpath(cand)
    raise FileNotFoundError("2d_rig.py not found (tried repo + workspace "
                            "shared dirs)")


_spec = importlib.util.spec_from_file_location("two_d_rig", _find_rig())
rig2d = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rig2d)


def build_lights():
    bpy.ops.object.light_add(type="SUN", location=(20, 30, 40))
    sun = bpy.context.active_object
    sun.name = "Sun"
    sun.data.energy = 3.0
    bpy.ops.object.light_add(type="AREA", location=(0, 25, 18))
    fill = bpy.context.active_object
    fill.name = "Fill"
    fill.data.energy = 120.0
    fill.data.size = 8.0
    return sun, fill


def key_lighting(sun, fill, world, frame, preset):
    """Keyframe the full lighting state (sun, fill, world) at one frame."""
    p = cm.LIGHTING[preset]
    sun.location = p["sun_loc"]
    sun.rotation_euler = (Vector((0, -3, 0)) - Vector(p["sun_loc"])
                          ).to_track_quat("-Z", "Y").to_euler()
    cm.kf(sun, frame, "location")
    cm.kf(sun, frame)
    sun.data.energy = p["sun_energy"]
    sun.data.keyframe_insert(data_path="energy", frame=frame)
    sun.data.color = p["sun_color"]
    sun.data.keyframe_insert(data_path="color", frame=frame)
    fill.data.energy = p["fill_energy"] * 300.0
    fill.data.keyframe_insert(data_path="energy", frame=frame)
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (*cm.hx(p["world_color"]), 1.0)
    bg.inputs["Color"].keyframe_insert(data_path="default_value",
                                       frame=frame)
    bg.inputs["Strength"].default_value = p["world_strength"]
    bg.inputs["Strength"].keyframe_insert(data_path="default_value",
                                          frame=frame)


def schedule_visibility(ctx):
    """Central visibility schedule. Visibility is ROOT SCALE (0.001 =
    hidden). Adjacent spans are MERGED into single calls (two
    visible_span calls sharing a boundary frame write conflicting keys).
    The lift arrow is NOT scheduled here — shot 3 keys its scale
    manually (pulse + vanish)."""
    vs = cm.visible_span
    H = cm.HIDDEN
    # engineers (2D humans) — S1 only. (S4 was planned with an engineer,
    # but the v1 stills showed a person at the wing macro distance would
    # sit behind the camera or fill the frame; the burrs carry S4 alone.)
    vs(ctx["eng1"]["placement"], 0, 215)
    vs(ctx["eng2"]["placement"], 0, 215)
    # hero jet: S2, S4+S5 (merged), S8
    vs(ctx["hero"]["root"], 216, 353)
    vs(ctx["hero"]["root"], 500, 777)
    vs(ctx["hero"]["root"], 971, 1031)
    # hero burrs: from S4 on (cover S4/S5/S8; parent hides them in between)
    vs(ctx["hero"]["burr_root"], 500, 1031)
    # hero S8 glued airflow + vortices: S8 only
    vs(ctx["hero"]["flow8_root"], 971, 1031)
    # smooth jets: S2 + S5; their S8 rigs never used
    for jet in (ctx["smooth1"], ctx["smooth2"]):
        vs(jet["root"], 216, 353)
        vs(jet["root"], 670, 777)
        cm.scale_at(jet["flow8_root"], 0, H)
        cm.scale_at(jet["flow8_root"], 1283, H)
    # airliner: S10 only
    vs(ctx["airliner"]["root"], 1100, 1283)
    # wing lab: S3, S6+S7 (merged), S9
    wl = ctx["winglab"]
    vs(wl["root"], 354, 499)
    vs(wl["root"], 778, 970)
    vs(wl["root"], 1032, 1099)
    vs(wl["lines_root"], 354, 499)
    vs(wl["lines_root"], 778, 970)
    vs(wl["fins_root"], 778, 970)
    vs(wl["fins_root"], 1032, 1099)
    vs(wl["vort_root"], 875, 970)
    vs(wl["gleam"], 1032, 1099)
    # model plane's S8 rig is never used
    cm.scale_at(ctx["hangar"]["model"]["flow8_root"], 0, H)
    cm.scale_at(ctx["hangar"]["model"]["flow8_root"], 1283, H)


def main():
    t0 = time.time()
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # ---- sets (built once, shared by all shots)
    hangar = props.build_hangar()
    airfield = props.build_airfield()
    winglab = props.build_wing_lab()
    clouds = props.build_clouds()
    sun, fill = build_lights()
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    world.use_nodes = True

    # ---- aircraft
    hero = props.build_jet("JetHero", (48, 0, 0.6), battered=True)
    smooth1 = props.build_jet("JetSmooth1", (47, -3.5, 0.7))
    smooth2 = props.build_jet("JetSmooth2", (47, 3.5, 0.7))
    airliner = props.build_airliner("Airliner", (48, 0, 26))

    # ---- 2D engineers (flat Grease Pencil humans — NEVER 3D figures)
    eng1 = rig2d.create_human(
        "Eng1", location=(-1.4, 1.6, 0), height=1.8,
        skin=(0.72, 0.48, 0.32), shirt=(0.25, 0.45, 0.65),
        pants=(0.20, 0.24, 0.40), hair=(0.12, 0.08, 0.06),
        shoe=(0.30, 0.20, 0.14), hat="cap", hat_color=(0.85, 0.70, 0.15))
    eng2 = rig2d.create_human(
        "Eng2", location=(1.1, 1.9, 0), height=1.75,
        skin=(0.85, 0.62, 0.45), shirt=(0.65, 0.35, 0.20),
        pants=(0.30, 0.28, 0.26), hair=(0.15, 0.10, 0.08),
        shoe=(0.25, 0.18, 0.12))

    ctx = dict(eng1=eng1, eng2=eng2, hero=hero, smooth1=smooth1,
               smooth2=smooth2, airliner=airliner, winglab=winglab,
               hangar=hangar, airfield=airfield, clouds=clouds,
               sun=sun, fill=fill, world=world)

    schedule_visibility(ctx)

    # ---- clouds drift slowly +X across the whole timeline
    for c in clouds:
        base = tuple(c.location)
        cm.loc_key(c, 0, base)
        cm.loc_key(c, 1283, (base[0] + 10, base[1], base[2]))
        cm.set_linear(c)

    # ---- lighting: key each shot's preset at its first AND last frame
    for _num, start, end, preset in cm.SHOTS:
        key_lighting(sun, fill, world, start, preset)
        key_lighting(sun, fill, world, end - 1, preset)

    # ---- the 10 shots, in timeline order
    cameras = []
    for i, fn in enumerate(shots.SHOTS, start=1):
        ts = time.time()
        info = fn(ctx)
        cameras.extend(info["cameras"])
        print("  shot %02d built in %.1fs" % (i, time.time() - ts))

    # ---- markers + camera binding (hard cuts)
    scene = bpy.context.scene
    for frame, cam in sorted(cameras):
        m = scene.timeline_markers.new(name="Shot_%04d" % frame,
                                       frame=frame)
        m.camera = cam
    scene.camera = sorted(cameras)[0][1]

    # ---- scene settings (final: 1080x1920, 30 fps, Eevee on Colab GPU)
    scene.frame_start = 0
    scene.frame_end = 1283
    scene.render.fps = 30
    scene.render.resolution_x = 1080
    scene.render.resolution_y = 1920
    scene.render.resolution_percentage = 100
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.image_settings.file_format = "PNG"

    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.normpath(os.path.join(here, "..", "scenes",
                                        "vortex.blend"))
    bpy.ops.wm.save_as_mainfile(filepath=out)

    n_mesh = sum(1 for o in scene.objects if o.type == "MESH")
    n_gp = sum(1 for o in scene.objects if o.type == "GPENCIL")
    n_curve = sum(1 for o in scene.objects if o.type == "CURVE")
    n_all = len(scene.objects)
    n_poly = sum(len(o.data.polygons) for o in scene.objects
                 if o.type == "MESH")
    n_actions = len(bpy.data.actions)
    print("BUILD ALL OK in %.1fs: %d objects (%d meshes, %d GP, %d curves), "
          "%d polys, %d actions, %d cameras, frames 0-1283"
          % (time.time() - t0, n_all, n_mesh, n_gp, n_curve, n_poly,
             n_actions, len(cameras)))
    print("saved:", out)


if __name__ == "__main__":
    main()
