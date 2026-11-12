# common.py — shared helpers for the V1 vortex-generators Blender short.
#
# Conventions (same as the chicken Blender short):
# - One scene, one 1284-frame timeline (frames 0-1283). Shots are HARD CUTS
#   at the marker frames in SHOTS (end is exclusive: shot N covers
#   [start, end-1]).
# - Objects are built ONCE by build_all.py and shared. Shot modules only
#   keyframe what they show. Teleports between shots are invisible (hard cut).
# - Visibility is done by ROOT SCALE (0.001 = hidden), never hide_render:
#   scaling the root scales the whole rig/group. Always key BOTH sides of a
#   visibility change. Adjacent spans must be MERGED (two visible_span calls
#   sharing a boundary frame write conflicting keys).
# - Timing comes from voice/words.json via SHOT_PLAN.md — never by feel.
# - FOV WARNING (measured 2026-11-12): with sensor_fit="VERTICAL" the
#   vertical FOV uses the 24 mm sensor HEIGHT, not the 36 mm width:
#   vertical half-angle = atan(12/lens_mm), horizontal half-angle =
#   atan(tan(12/lens_mm) * 9/16). At 36 mm the horizontal half-FOV is
#   only ~10.7 deg (an 8 m jet needs ~27 m distance at 28 mm to fit at
#   60% of frame width). The v1 cameras were all ~1.5x too close because
#   of this; distances below are computed from the CORRECT formula.
import math

import bpy
from mathutils import Matrix, Vector

FRAME_END = 1284            # timeline is frames 0..1283
HIDDEN = 0.001              # root scale that reads as "not there"

# (shot number, start frame, end frame [exclusive], lighting preset)
SHOTS = [
    (1, 0, 216, "hangar"),
    (2, 216, 354, "day"),
    (3, 354, 500, "day"),
    (4, 500, 670, "day"),
    (5, 670, 778, "day"),
    (6, 778, 875, "day"),
    (7, 875, 971, "day"),
    (8, 971, 1032, "day"),
    (9, 1032, 1100, "day"),
    (10, 1100, 1284, "day"),
]

DAY = dict(
    sun_energy=3.0, sun_color=(1.0, 0.96, 0.88),
    sun_loc=(20, 30, 40), fill_energy=0.35,
    world_color="#79a8e0", world_strength=1.0,
)
HANGAR = dict(
    sun_energy=1.8, sun_color=(1.0, 0.88, 0.70),
    sun_loc=(6, 12, 10), fill_energy=0.5,
    world_color="#8a7a68", world_strength=0.6,
)
LIGHTING = {"day": DAY, "hangar": HANGAR}


# ---------------------------------------------------------------- colour

def _srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hx(hexcol):
    """'#rrggbb' -> linear RGB tuple for Blender colour inputs."""
    h = hexcol.lstrip("#")
    return tuple(_srgb_to_linear(int(h[i:i + 2], 16) / 255.0) for i in (0, 2, 4))


# ---------------------------------------------------------------- materials

_mat_cache = {}


def flat_mat(name, hexcol, roughness=0.92):
    """Flat Principled material (Eevee + Cycles safe). Cached by name."""
    if name in _mat_cache:
        return _mat_cache[name]
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*hx(hexcol), 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Specular IOR Level"].default_value = 0.3
    mat.diffuse_color = (*hx(hexcol), 1.0)  # Workbench MATERIAL colour mode
    _mat_cache[name] = mat
    return mat


def emissive_mat(name, hexcol, strength=2.0):
    """Flat emissive material (glow bits: lift arrow tip, gleam bar)."""
    if name in _mat_cache:
        return _mat_cache[name]
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*hx(hexcol), 1.0)
    bsdf.inputs["Emission Color"].default_value = (*hx(hexcol), 1.0)
    bsdf.inputs["Emission Strength"].default_value = strength
    bsdf.inputs["Roughness"].default_value = 0.6
    mat.diffuse_color = (*hx(hexcol), 1.0)
    _mat_cache[name] = mat
    return mat


# ---------------------------------------------------------------- mesh utils

def _link(obj):
    bpy.context.collection.objects.link(obj)
    return obj


def new_empty(name, parent=None, loc=(0, 0, 0)):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = "PLAIN_AXES"
    e.empty_display_size = 0.08
    _link(e)
    if parent is not None:
        e.parent = parent
    e.location = loc
    return e


def _bake_scale(obj, sx, sy, sz):
    obj.data.transform(Matrix.Diagonal(Vector((sx, sy, sz, 1.0))))
    obj.data.update()


def _shade(obj, smooth=True):
    for p in obj.data.polygons:
        p.use_smooth = smooth


def _finish(obj, mat, parent, loc, rot):
    if parent is not None:
        obj.parent = parent
    obj.location = loc
    obj.rotation_euler = rot
    if mat is not None:
        obj.data.materials.append(mat)
    return obj


def add_sphere(name, r, mat, parent=None, loc=(0, 0, 0), rot=(0, 0, 0),
               scale=(1, 1, 1), seg=20, rings=14):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=seg, ring_count=rings, radius=r, location=(0, 0, 0))
    obj = bpy.context.active_object
    obj.name = name
    _bake_scale(obj, *scale)
    _shade(obj, True)
    return _finish(obj, mat, parent, loc, rot)


def add_cylinder(name, r, depth, mat, parent=None, loc=(0, 0, 0),
                 rot=(0, 0, 0), verts=16):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=verts, radius=r, depth=depth, location=(0, 0, 0))
    obj = bpy.context.active_object
    obj.name = name
    _shade(obj, True)
    return _finish(obj, mat, parent, loc, rot)


def add_cone(name, r1, r2, depth, mat, parent=None, loc=(0, 0, 0),
             rot=(0, 0, 0), verts=16):
    bpy.ops.mesh.primitive_cone_add(
        vertices=verts, radius1=r1, radius2=r2, depth=depth,
        location=(0, 0, 0))
    obj = bpy.context.active_object
    obj.name = name
    _shade(obj, True)
    return _finish(obj, mat, parent, loc, rot)


def add_box(name, dims, mat, parent=None, loc=(0, 0, 0), rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0))
    obj = bpy.context.active_object
    obj.name = name
    _bake_scale(obj, dims[0], dims[1], dims[2])
    _shade(obj, False)
    return _finish(obj, mat, parent, loc, rot)


def add_torus(name, major_r, minor_r, mat, parent=None, loc=(0, 0, 0),
              rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major_r, minor_radius=minor_r, location=(0, 0, 0))
    obj = bpy.context.active_object
    obj.name = name
    _shade(obj, True)
    return _finish(obj, mat, parent, loc, rot)


def add_plane(name, size, mat, parent=None, loc=(0, 0, 0), rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, 0))
    obj = bpy.context.active_object
    obj.name = name
    _shade(obj, False)
    return _finish(obj, mat, parent, loc, rot)


# ---------------------------------------------------------------- keyframes

def kf(obj, frame, data_path="rotation_euler"):
    obj.keyframe_insert(data_path=data_path, frame=frame)


def set_linear(obj):
    if obj.animation_data and obj.animation_data.action:
        for fc in obj.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"


def set_linear_range(obj, f_min, f_max):
    if obj.animation_data and obj.animation_data.action:
        for fc in obj.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                if f_min <= kp.co.x <= f_max:
                    kp.interpolation = "LINEAR"


def loc_key(obj, frame, loc):
    obj.location = loc
    kf(obj, frame, "location")


def rot_key(obj, frame, rot):
    """Keyframe rotation_euler (radians tuple)."""
    obj.rotation_euler = rot
    kf(obj, frame)


def rot_z_key(obj, frame, deg):
    obj.rotation_euler[2] = math.radians(deg)
    obj.keyframe_insert(data_path="rotation_euler", index=2, frame=frame)


def scale_key(obj, frame, s):
    obj.scale = (s, s, s)
    kf(obj, frame, "scale")


def scale_at(obj, frame, s):
    scale_key(obj, frame, s)


# ---------------------------------------------------------------- visibility

def visible_span(obj, f_start, f_end, base=1.0, fade_in=0, fade_out=0):
    """Object visible (scale=base) between f_start and f_end inclusive,
    hidden (scale 0.001) outside. Keys both sides of every transition.
    NEVER call twice with adjacent spans — merge them into one call."""
    if f_start > 0:
        scale_at(obj, f_start - 1, HIDDEN)
    if fade_in > 0:
        scale_at(obj, f_start, HIDDEN)
        scale_at(obj, f_start + fade_in, base)
    else:
        scale_at(obj, f_start, base)
    if fade_out > 0:
        scale_at(obj, f_end - fade_out, base)
        scale_at(obj, f_end, HIDDEN)
    else:
        scale_at(obj, f_end, base)
    if f_end < FRAME_END - 1:
        scale_at(obj, f_end + 1, HIDDEN)


# ---------------------------------------------------------------- camera

def _catmull_rom(p0, p1, p2, p3, u):
    return 0.5 * ((2 * p1) + (-p0 + p2) * u
                  + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u
                  + (-p0 + 3 * p1 - 3 * p2 + p3) * u * u * u)


def _sample_keys(pts, f):
    if f <= pts[0][0]:
        return pts[0][1], pts[0][2]
    if f >= pts[-1][0]:
        return pts[-1][1], pts[-1][2]
    i = next(i for i in range(len(pts) - 1)
             if pts[i][0] <= f < pts[i + 1][0])
    u = (f - pts[i][0]) / (pts[i + 1][0] - pts[i][0])
    p0 = pts[max(0, i - 1)][1]
    p1 = pts[i][1]
    p2 = pts[i + 1][1]
    p3 = pts[min(len(pts) - 1, i + 2)][1]
    loc = _catmull_rom(p0, p1, p2, p3, u)
    lens = pts[i][2] + (pts[i + 1][2] - pts[i][2]) * u
    return loc, lens


def build_shot_camera(name, cam_keys, focus_keys, f_start, f_end,
                      sample=3):
    """Build one marker-bound shot camera.

    cam_keys: [(frame, (x, y, z), lens_mm)] — Catmull-Rom path.
    focus_keys: [(frame, (x, y, z))] — Track-To focus path (same sampling).
    Returns (camera object, focus empty).
    """
    cam_data = bpy.data.cameras.new(name)
    cam_data.lens = cam_keys[0][2]
    cam_data.sensor_fit = "VERTICAL"
    cam_data.sensor_width = 36
    cam_data.clip_start = 0.1
    cam_data.clip_end = 300
    cam = bpy.data.objects.new(name, cam_data)
    bpy.context.collection.objects.link(cam)
    focus = new_empty(name + "_Focus", loc=focus_keys[0][1])
    con = cam.constraints.new(type="TRACK_TO")
    con.target = focus
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"

    pts = [(f, Vector(loc), lens) for f, loc, lens in cam_keys]
    fpts = [(f, Vector(loc), 0.0) for f, loc in focus_keys]
    for f in range(f_start, f_end + 1, sample):
        loc, lens = _sample_keys(pts, f)
        cam.location = loc
        kf(cam, f, "location")
        cam_data.lens = lens
        cam_data.keyframe_insert(data_path="lens", frame=f)
        floc, _ = _sample_keys(fpts, f)
        focus.location = floc
        kf(focus, f, "location")
    if (f_end - f_start) % sample:
        loc, lens = _sample_keys(pts, f_end)
        cam.location = loc
        kf(cam, f_end, "location")
        cam_data.lens = lens
        cam_data.keyframe_insert(data_path="lens", frame=f_end)
        floc, _ = _sample_keys(fpts, f_end)
        focus.location = floc
        kf(focus, f_end, "location")
    set_linear(cam)
    set_linear(focus)
    if cam_data.animation_data and cam_data.animation_data.action:
        for fc in cam_data.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
    return cam, focus


# ---------------------------------------------------------------- 2D rig facing

def face_camera(rig, frame, char_xy, cam_xy):
    """Keyframe a 2D rig's placement yaw so the flat character faces a
    camera at cam_xy (world XY). The drawing's front normal is
    placement-local -Y, so yaw phi gives forward (sin phi, -cos phi)."""
    dx = cam_xy[0] - char_xy[0]
    dy = cam_xy[1] - char_xy[1]
    phi = math.atan2(dx, -dy)
    rig["placement"].rotation_euler = (0, 0, phi)
    kf(rig["placement"], frame)


def place_rig(rig, frame, loc):
    """Keyframe a 2D rig's placement location (x, y, z)."""
    rig["placement"].location = loc
    kf(rig["placement"], frame, "location")


def joint_rot(obj, frame, z_deg=None, x_deg=None, y_deg=None, interp=None):
    """Keyframe one rotation component of a 2D-rig joint empty."""
    if z_deg is not None:
        obj.rotation_euler[2] = math.radians(z_deg)
        obj.keyframe_insert(data_path="rotation_euler", index=2,
                            frame=frame)
    if x_deg is not None:
        obj.rotation_euler[0] = math.radians(x_deg)
        obj.keyframe_insert(data_path="rotation_euler", index=0,
                            frame=frame)
    if y_deg is not None:
        obj.rotation_euler[1] = math.radians(y_deg)
        obj.keyframe_insert(data_path="rotation_euler", index=1,
                            frame=frame)
    if interp:
        ad = obj.animation_data
        if ad and ad.action:
            for fc in ad.action.fcurves:
                if fc.data_path == "rotation_euler":
                    for kp in fc.keyframe_points:
                        if abs(kp.co.x - frame) < 0.5:
                            kp.interpolation = interp
