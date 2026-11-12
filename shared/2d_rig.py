"""
2d_rig.py — Flat 2D human characters for Blender explainer shorts (@ExplainerMaan).

TECHNIQUE (Milestone 0 winner): Grease Pencil (legacy GP v2 in Blender 4.2).
One GP object per body part, parented in a joint hierarchy under a root empty
that is rotated 90 deg about X so the flat drawings stand upright facing the
camera. Limbs animate by rotating joint empties; the drawings are vector
strokes/fills, so outlines stay crisp at any resolution and there is no 3D
shading / black-shell outline problem. Worlds/scenery stay 3D meshes;
HUMANS are always flat 2D. Never substitute 3D figures.

Calibration (measured 2026-11-12 in Blender 4.2.23, Workbench):
- GP 3DSPACE line_width is a true world-space size: it doubles in pixels
  when render resolution doubles (540 -> 1080) and stays constant in world
  units when camera distance halves (9 -> 4.5 units). Conversion:
  line_width ~= world_units * 1500. All widths below derive from the
  character height H so any size stays proportional.
- Materials: a fresh bpy.data.materials.new() has .grease_pencil == None
  (and .is_grease_pencil is read-only). Working GP materials are made by
  copying the "Black" material that bpy.ops.object.gpencil_add() creates.
  This module does that once (hidden "_GP_Template" object) and caches it.
- GP objects are drawn in local XY (Y-up) and the rig root rotates them
  upright. The placement empty carries a 180 deg base yaw so the drawing
  faces a +Y camera (see the note at create_human: a Damped Track alone
  took the pitch flip and rendered the character UPSIDE DOWN). After that
  yaw, root-local +Z points toward the camera, so parts in front use
  POSITIVE local Z offsets (arms/head) and parts behind use negative
  (thighs under the torso). Small offsets also prevent z-fighting between
  overlapping strokes (hair over head, shoe over shin).

USAGE (inside a Blender python script, e.g. build_proof.py):

    import sys; sys.path.insert(0, "/home/hatch/workspace/blender_shorts_4/shared")
    import importlib, two_d_rig  # NOTE: module file is 2d_rig.py; import via importlib
    # (see build_proof.py for the exact import snippet)

    rig = two_d_rig.create_human(
        "Asha", location=(0, 0, 0), height=3.2,
        skin=(0.72, 0.48, 0.32), shirt=(0.10, 0.55, 0.60),
        pants=(0.20, 0.24, 0.40), hair=(0.12, 0.08, 0.06),
        shoe=(0.30, 0.20, 0.14), hat="cap", hat_color=(0.75, 0.20, 0.20))
    two_d_rig.walk_cycle(rig, 1, 41, cycle_frames=20)
    two_d_rig.wave(rig, 41, 56, arm="R")
    two_d_rig.head_turn(rig, 56, 68, angle_deg=38)
    two_d_rig.add_billboard(rig, bpy.context.scene.camera)  # optional

RIG DICT keys: placement, root, hips, torso, head_pivot, head,
shoulder{"L","R"}, upper_arm{"L","R"}, elbow{"L","R"}, forearm{"L","R"},
hip_joint{"L","R"}, thigh{"L","R"}, knee{"L","R"}, shin{"L","R"}, dims, H.
"L" = +X side (the character's own left; appears screen-right when
facing the camera, as a real person's left does), "R" = -X side.
"""

import bpy
import math
from mathutils import Vector

# ---------------------------------------------------------------------------
# Calibration constants
# ---------------------------------------------------------------------------
WIDTH_PER_UNIT = 1500.0  # GP 3DSPACE line_width per world unit (measured)

# Character proportions, as fractions of total height H (Y-up, feet at y=0)
P = {
    "hip_h": 0.52,        # hip joint height
    "torso_bot": 0.50, "torso_top": 0.76, "torso_w": 0.27, "torso_r": 0.05,
    "shoulder_h": 0.72, "sh_half": 0.135,
    "neck_h": 0.74,
    "head_r": 0.13, "head_cy": 0.87,
    "upper": 0.17, "fore": 0.16, "hand_r": 0.035,
    "thigh": 0.26, "shin": 0.26, "hip_half": 0.05,
    "shoe_rx": 0.055, "shoe_ry": 0.035,
    # stroke widths as fractions of H
    "w_outline": 0.014, "w_leg": 0.055, "w_arm": 0.047, "w_neck": 0.030,
    "w_smile": 0.009, "w_brow": 0.008, "w_detail": 0.008,
}

_TEMPLATE_MAT = None
_MAT_CACHE = {}


# ---------------------------------------------------------------------------
# Grease Pencil materials
# ---------------------------------------------------------------------------
def _template_material():
    """Return a working GP material (copy source). Created once per session
    from the operator-made GP object's default 'Black' material."""
    global _TEMPLATE_MAT
    if _TEMPLATE_MAT is not None:
        return _TEMPLATE_MAT
    # find an existing template object (e.g. re-run in same .blend)
    tpl = bpy.data.objects.get("_GP_Template")
    if tpl is not None and tpl.type == 'GPENCIL' and len(tpl.data.materials) > 0:
        _TEMPLATE_MAT = tpl.data.materials[0]
        return _TEMPLATE_MAT
    prev_active = bpy.context.view_layer.objects.active
    prev_sel = [o for o in bpy.context.selected_objects]
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.gpencil_add(location=(0, 0, -50), type='EMPTY')
    tpl = bpy.context.active_object
    tpl.name = "_GP_Template"
    tpl.hide_viewport = True
    tpl.hide_render = True
    _TEMPLATE_MAT = tpl.data.materials[0]
    bpy.ops.object.select_all(action='DESELECT')
    for o in prev_sel:
        o.select_set(True)
    if prev_active is not None:
        bpy.context.view_layer.objects.active = prev_active
    return _TEMPLATE_MAT


def gp_material(name, stroke_rgb, fill_rgb=None, show_fill=True, show_stroke=True):
    """Create (or reuse) a GP material with flat fill + outline stroke.

    stroke_rgb / fill_rgb: (r, g, b) 0..1 tuples. Alpha is always 1.
    """
    key = (name, tuple(stroke_rgb), tuple(fill_rgb) if fill_rgb else None,
           show_fill, show_stroke)
    if key in _MAT_CACHE:
        return _MAT_CACHE[key]
    mat = _template_material().copy()
    mat.name = name
    g = mat.grease_pencil
    g.color = (*stroke_rgb, 1.0)
    g.fill_color = (*(fill_rgb if fill_rgb is not None else stroke_rgb), 1.0)
    g.show_fill = show_fill
    g.show_stroke = show_stroke
    g.fill_style = 'SOLID'
    _MAT_CACHE[key] = mat
    return mat


# ---------------------------------------------------------------------------
# GP object + drawing primitives
# ---------------------------------------------------------------------------
def _new_gp_object(name, parent, location=(0, 0, 0)):
    gp = bpy.data.grease_pencils.new(name + "_data")
    gp.stroke_depth_order = '3D'
    obj = bpy.data.objects.new(name, gp)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = parent
    obj.location = location
    layer = gp.layers.new("Draw")
    layer.frames.new(0)
    return obj


def _mat_index(gp_obj, mat):
    mats = gp_obj.data.materials
    for i, m in enumerate(mats):
        if m == mat:
            return i
    mats.append(mat)
    return len(mats) - 1


def _stroke(gp_obj, mat, pts, width, cyclic=False, z=0.0, cap='ROUND'):
    """Add one stroke to frame 0. pts: list of (x, y) in object-local space."""
    frame = gp_obj.data.layers[0].frames[0]
    s = frame.strokes.new()
    s.points.add(len(pts))
    for i, (x, y) in enumerate(pts):
        s.points[i].co = Vector((x, y, z))
        s.points[i].pressure = 1.0
        s.points[i].strength = 1.0
    s.material_index = _mat_index(gp_obj, mat)
    s.line_width = max(1, int(round(width)))
    s.use_cyclic = cyclic
    s.display_mode = '3DSPACE'
    s.start_cap_mode = cap
    s.end_cap_mode = cap
    return s


def _circle_pts(cx, cy, r, n=28, a0=0.0, a1=2 * math.pi):
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / (n - 1)),
             cy + r * math.sin(a0 + (a1 - a0) * i / (n - 1))) for i in range(n)]


def _ellipse_pts(cx, cy, rx, ry, n=24):
    return [(cx + rx * math.cos(2 * math.pi * i / n),
             cy + ry * math.sin(2 * math.pi * i / n)) for i in range(n)]


def _rrect_pts(cx, cy, w, h, r, n_seg=6):
    pts = []
    corners = [(cx + w / 2 - r, cy + h / 2 - r, 0),
               (cx - w / 2 + r, cy + h / 2 - r, 90),
               (cx - w / 2 + r, cy - h / 2 + r, 180),
               (cx + w / 2 - r, cy - h / 2 + r, 270)]
    for ccx, ccy, deg in corners:
        for i in range(n_seg + 1):
            a = math.radians(deg + 90 * i / n_seg)
            pts.append((ccx + r * math.cos(a), ccy + r * math.sin(a)))
    return pts


def _arc_band_pts(cx, cy, r_out, r_in, a0_deg, a1_deg, n=14):
    """Closed band between two arcs (hair cap, hat dome)."""
    pts = _circle_pts(cx, cy, r_out, n, math.radians(a0_deg), math.radians(a1_deg))
    pts += _circle_pts(cx, cy, r_in, n, math.radians(a1_deg), math.radians(a0_deg))
    return pts


def _empty(name, parent, location=(0, 0, 0)):
    o = bpy.data.objects.new(name, None)
    o.empty_display_type = 'PLAIN_AXES'
    o.empty_display_size = 0.25
    bpy.context.scene.collection.objects.link(o)
    o.parent = parent
    o.location = location
    return o


# ---------------------------------------------------------------------------
# Character construction
# ---------------------------------------------------------------------------
def create_human(name, location=(0, 0, 0), height=3.2,
                 skin=(0.98, 0.80, 0.62), shirt=(0.15, 0.55, 0.75),
                 pants=(0.25, 0.30, 0.55), hair=(0.25, 0.15, 0.08),
                 shoe=(0.15, 0.12, 0.10), outline=(0.10, 0.08, 0.08),
                 hat=None, hat_color=(0.75, 0.20, 0.20), facing_deg=0.0):
    """Build one flat 2D human. Returns the rig dict (see module docstring).

    hat: None or "cap" (baseball cap in hat_color, brim to the character's
    left = screen right). facing_deg rotates the whole character about the
    vertical axis (0 = facing the camera at +Y; keep within ~+-60 deg or
    use add_billboard, since a flat character goes edge-on at 90 deg).
    """
    H = float(height)
    w = {k: v * H * WIDTH_PER_UNIT for k, v in P.items() if k.startswith("w_")}

    # materials (shared across characters with same colours)
    m_outline = gp_material("GP_Outline", outline, show_fill=False)
    m_skin = gp_material("GP_Skin", outline, skin)
    m_shirt = gp_material("GP_Shirt", outline, shirt)
    m_pants = gp_material("GP_Pants", outline, pants)
    m_hair = gp_material("GP_Hair", outline, hair)
    m_shoe = gp_material("GP_Shoe", outline, shoe)
    m_eye = gp_material("GP_Eye", outline, outline, show_stroke=False)
    m_hat = gp_material("GP_Hat", outline, hat_color) if hat else None

    # --- hierarchy: placement (world pos/facing) -> root (rot X 90) -> parts
    placement = _empty(name + "_place", None, location)
    # Base yaw 180 deg: the drawing's front normal is placement-local -Y, so
    # without this the character faces -Y (away from a +Y camera). The old
    # code relied on the billboard Damped Track to fix the 180 deg gap, but a
    # 180 deg Damped Track is degenerate and Blender took the PITCH flip,
    # rendering the character UPSIDE DOWN (proven by the 2026-11-12 stills).
    placement.rotation_euler = (0, 0, math.radians(180.0 + facing_deg))
    root = _empty(name + "_root", placement)
    root.rotation_euler = (math.radians(90), 0, 0)
    hips = _empty(name + "_hips", root, (0, P["hip_h"] * H, 0))

    rig = {"name": name, "placement": placement, "root": root, "hips": hips,
           "H": H, "dims": dict(P), "billboard": None,
           "shoulder": {}, "upper_arm": {}, "elbow": {}, "forearm": {},
           "hip_joint": {}, "thigh": {}, "knee": {}, "shin": {}}

    # --- torso (child of hips; drawn upward from hip level) ---
    torso = _new_gp_object(name + "_torso", hips, (0, 0, 0))
    cy = (P["torso_bot"] + P["torso_top"]) / 2 * H - P["hip_h"] * H
    th = (P["torso_top"] - P["torso_bot"]) * H
    _stroke(torso, m_shirt,
            _rrect_pts(0, cy, P["torso_w"] * H, th, P["torso_r"] * H),
            w["w_outline"], cyclic=True)
    # neck (skin, tucks behind head)
    ny0 = (P["neck_h"] - P["hip_h"]) * H - 0.02 * H
    ny1 = (P["neck_h"] - P["hip_h"]) * H + 0.06 * H
    _stroke(torso, m_skin, [(0, ny0), (0, ny1)], w["w_neck"])
    # collar V + buttons (detail strokes, slightly in front)
    _stroke(torso, m_outline,
            [(-0.05 * H, (P["torso_top"] - 0.005) * H - P["hip_h"] * H),
             (0, (P["torso_top"] - 0.05) * H - P["hip_h"] * H),
             (0.05 * H, (P["torso_top"] - 0.005) * H - P["hip_h"] * H)],
            w["w_detail"], z=0.004)
    for by in (0.60, 0.68):
        _stroke(torso, m_eye,
                _circle_pts(0, by * H - P["hip_h"] * H, 0.012 * H, 8),
                1, cyclic=True, z=0.004)
    rig["torso"] = torso

    # --- head (pivot at neck; head drawn above it) ---
    head_pivot = _empty(name + "_head_pivot", hips,
                        (0, (P["neck_h"] - P["hip_h"]) * H, 0))
    head = _new_gp_object(name + "_head", head_pivot, (0, 0, 0.02))
    hcy = (P["head_cy"] - P["neck_h"]) * H
    hr = P["head_r"] * H
    _stroke(head, m_skin, _circle_pts(0, hcy, hr, 30), w["w_outline"], cyclic=True)
    # hair: filled arc band over the top of the head
    _stroke(head, m_hair,
            _arc_band_pts(0, hcy, hr * 1.02, hr * 0.62, 12, 168),
            w["w_outline"], cyclic=True, z=0.005)
    # eyes + brows + smile
    for sx in (-1, 1):
        _stroke(head, m_eye,
                _circle_pts(sx * 0.045 * H, hcy + 0.02 * H, 0.014 * H, 10),
                1, cyclic=True, z=0.008)
        _stroke(head, m_outline,
                _circle_pts(sx * 0.045 * H, hcy + 0.055 * H, 0.03 * H, 6,
                            math.radians(30), math.radians(150)),
                w["w_brow"], z=0.008)
    smile = [(x, hcy - 0.045 * H - 0.02 * H * (1 - (x / (0.05 * H)) ** 2))
             for x in [i * 0.01 * H - 0.05 * H for i in range(11)]]
    _stroke(head, m_outline, smile, w["w_smile"], z=0.008)
    # optional cap: dome + brim (in front of the hair band)
    if hat == "cap":
        _stroke(head, m_hat,
                _arc_band_pts(0, hcy + 0.01 * H, hr * 1.06, hr * 0.55, 8, 172),
                w["w_outline"], cyclic=True, z=0.012)
        _stroke(head, m_hat,
                _rrect_pts(0.10 * H, hcy + 0.055 * H, 0.16 * H, 0.035 * H, 0.015 * H),
                w["w_outline"], cyclic=True, z=0.012)
    rig["head_pivot"] = head_pivot
    rig["head"] = head

    # --- arms ---
    for side, sx in (("L", 1), ("R", -1)):
        sh = _empty(f"{name}_shoulder_{side}", hips,
                    (sx * P["sh_half"] * H, (P["shoulder_h"] - P["hip_h"]) * H, 0.03))
        ua = _new_gp_object(f"{name}_upper_arm_{side}", sh, (0, 0, 0))
        _stroke(ua, m_shirt, [(0, 0), (0, -P["upper"] * H)], w["w_arm"])
        el = _empty(f"{name}_elbow_{side}", ua, (0, -P["upper"] * H, 0.01))
        fa = _new_gp_object(f"{name}_forearm_{side}", el, (0, 0, 0))
        _stroke(fa, m_skin, [(0, 0), (0, -P["fore"] * H)], w["w_arm"] * 0.9)
        _stroke(fa, m_skin,
                _circle_pts(0, -P["fore"] * H - 0.01 * H, P["hand_r"] * H, 16),
                w["w_outline"], cyclic=True, z=0.005)
        rig["shoulder"][side] = sh
        rig["upper_arm"][side] = ua
        rig["elbow"][side] = el
        rig["forearm"][side] = fa

    # --- legs ---
    for side, sx in (("L", 1), ("R", -1)):
        hj = _empty(f"{name}_hip_{side}", hips,
                    (sx * P["hip_half"] * H, 0, -0.03))
        th = _new_gp_object(f"{name}_thigh_{side}", hj, (0, 0, 0))
        _stroke(th, m_pants, [(0, 0), (0, -P["thigh"] * H)], w["w_leg"])
        kn = _empty(f"{name}_knee_{side}", th, (0, -P["thigh"] * H, 0))
        sn = _new_gp_object(f"{name}_shin_{side}", kn, (0, 0, 0))
        _stroke(sn, m_pants, [(0, 0), (0, -P["shin"] * H)], w["w_leg"])
        _stroke(sn, m_shoe,
                _ellipse_pts(0.01 * H, -P["shin"] * H + 0.01 * H,
                             P["shoe_rx"] * H, P["shoe_ry"] * H, 20),
                w["w_outline"], cyclic=True, z=0.005)
        rig["hip_joint"][side] = hj
        rig["thigh"][side] = th
        rig["knee"][side] = kn
        rig["shin"][side] = sn

    return rig


# ---------------------------------------------------------------------------
# Keyframe helpers
# ---------------------------------------------------------------------------
def _key(obj, path, index, frame, value, interp=None):
    if path == "rotation_euler":
        obj.rotation_euler[index] = value
    elif path == "location":
        obj.location[index] = value
    elif path == "scale":
        obj.scale[index] = value
    else:
        raise ValueError(f"unsupported path {path}")
    obj.keyframe_insert(data_path=path, index=index, frame=frame)
    if interp:
        _set_interp(obj, path, index, frame, interp)


def _set_interp(obj, path, index, frame, interp):
    ad = obj.animation_data
    if not ad or not ad.action:
        return
    for fc in ad.action.fcurves:
        if fc.data_path == path and fc.array_index == index:
            for kp in fc.keyframe_points:
                if abs(kp.co.x - frame) < 0.5:
                    kp.interpolation = interp


def _rot(obj, frame, z_deg=None, y_deg=None, x_deg=None, interp=None):
    if z_deg is not None:
        _key(obj, "rotation_euler", 2, frame, math.radians(z_deg), interp)
    if y_deg is not None:
        _key(obj, "rotation_euler", 1, frame, math.radians(y_deg), interp)
    if x_deg is not None:
        _key(obj, "rotation_euler", 0, frame, math.radians(x_deg), interp)


def settle_neutral(rig, frame, interp='BEZIER'):
    """Key every joint back to its rest pose at `frame`."""
    for side in ("L", "R"):
        _rot(rig["shoulder"][side], frame, z_deg=0, interp=interp)
        _rot(rig["elbow"][side], frame, z_deg=0, interp=interp)
        _rot(rig["hip_joint"][side], frame, z_deg=0, interp=interp)
        _rot(rig["knee"][side], frame, z_deg=0, interp=interp)
    _rot(rig["head_pivot"], frame, z_deg=0, y_deg=0, interp=interp)
    _rot(rig["torso"], frame, z_deg=0, interp=interp)
    _key(rig["hips"], "location", 1, frame, P["hip_h"] * rig["H"], interp)


# ---------------------------------------------------------------------------
# Animation drivers
# ---------------------------------------------------------------------------
def walk_cycle(rig, start, end, cycle_frames=20, swing_deg=26, knee_deg=30,
               arm_deg=16, bob=0.05):
    """Front-view in-place walk (march-style: each leg swings out on its own
    side with alternating knee lifts, arms counter-swing, hips bob).
    (start, end) should span whole cycles: end = start + n*cycle_frames.
    Poses keyed at quarter-cycle points, LINEAR between them."""
    H = rig["H"]
    hip_y = P["hip_h"] * H
    # quarter poses: (L thigh, R thigh, L knee, R knee, L arm, R arm, hip dy, torso z)
    poses = [
        (swing_deg, -4, -8, knee_deg, -arm_deg, arm_deg * 0.6, 0.0, -2),
        (12, -14, -knee_deg, 8, 6, -12, bob, 0),
        (4, -swing_deg, -knee_deg, 8, arm_deg, -arm_deg * 0.6, 0.0, 2),
        (14, -12, -8, knee_deg, -6, 12, bob, 0),
    ]
    q = cycle_frames // 4
    n_cycles = max(1, round((end - start) / cycle_frames))
    for c in range(n_cycles):
        base = start + c * cycle_frames
        for i, p in enumerate(poses):
            f = base + i * q
            _rot(rig["hip_joint"]["L"], f, z_deg=p[0], interp='LINEAR')
            _rot(rig["hip_joint"]["R"], f, z_deg=p[1], interp='LINEAR')
            _rot(rig["knee"]["L"], f, z_deg=p[2], interp='LINEAR')
            _rot(rig["knee"]["R"], f, z_deg=p[3], interp='LINEAR')
            _rot(rig["shoulder"]["L"], f, z_deg=p[4], interp='LINEAR')
            _rot(rig["shoulder"]["R"], f, z_deg=p[5], interp='LINEAR')
            _rot(rig["elbow"]["L"], f, z_deg=-8, interp='LINEAR')
            _rot(rig["elbow"]["R"], f, z_deg=8, interp='LINEAR')
            _key(rig["hips"], "location", 1, f, hip_y + p[6], 'LINEAR')
            _rot(rig["torso"], f, z_deg=p[7], interp='LINEAR')
    # closing key = pose 0, so the loop is seamless
    f = start + n_cycles * cycle_frames
    p = poses[0]
    _rot(rig["hip_joint"]["L"], f, z_deg=p[0], interp='LINEAR')
    _rot(rig["hip_joint"]["R"], f, z_deg=p[1], interp='LINEAR')
    _rot(rig["knee"]["L"], f, z_deg=p[2], interp='LINEAR')
    _rot(rig["knee"]["R"], f, z_deg=p[3], interp='LINEAR')
    _rot(rig["shoulder"]["L"], f, z_deg=p[4], interp='LINEAR')
    _rot(rig["shoulder"]["R"], f, z_deg=p[5], interp='LINEAR')
    _key(rig["hips"], "location", 1, f, hip_y + p[6], 'LINEAR')
    _rot(rig["torso"], f, z_deg=p[7], interp='LINEAR')


def wave(rig, start, end, arm="R", waves=3):
    """Raise one arm up-out and wave it. Legs/other arm settle to neutral
    during the raise. start/end in frames; needs >= ~12 frames."""
    other = "L" if arm == "R" else "R"
    sign = -1 if arm == "R" else 1  # R arm (screen right) raises with -Z rot
    raise_end = start + 6
    lower_start = end - 6
    # settle everything neutral at raise_end (legs, other arm, head, hips)
    settle_neutral(rig, raise_end, interp='BEZIER')
    # raise the waving arm (overrides settle key on that shoulder/elbow)
    _rot(rig["shoulder"][arm], raise_end, z_deg=sign * 150, interp='BEZIER')
    _rot(rig["elbow"][arm], raise_end, z_deg=sign * -15, interp='BEZIER')
    # wave: oscillate the forearm
    span = max(6, lower_start - raise_end)
    n_half = waves * 2
    for i in range(n_half + 1):
        f = raise_end + span * i / n_half
        bend = -15 + (25 if i % 2 == 0 else -25)
        _rot(rig["elbow"][arm], round(f), z_deg=sign * bend, interp='BEZIER')
    # hold shoulder up through the wave, then lower
    _rot(rig["shoulder"][arm], lower_start, z_deg=sign * 150, interp='BEZIER')
    _rot(rig["elbow"][arm], lower_start, z_deg=sign * -15, interp='BEZIER')
    settle_neutral(rig, end, interp='BEZIER')
    # slight head tilt toward the waving arm while waving
    _rot(rig["head_pivot"], raise_end + 2, z_deg=sign * -6, interp='BEZIER')
    _rot(rig["head_pivot"], lower_start, z_deg=sign * -6, interp='BEZIER')


def point(rig, start, end, arm="R"):
    """Point one arm straight out to the side, hold, lower."""
    other = "L" if arm == "R" else "R"
    sign = -1 if arm == "R" else 1
    raise_end = start + 5
    lower_start = end - 5
    settle_neutral(rig, raise_end, interp='BEZIER')
    _rot(rig["shoulder"][arm], raise_end, z_deg=sign * 88, interp='BEZIER')
    _rot(rig["elbow"][arm], raise_end, z_deg=0, interp='BEZIER')
    _rot(rig["shoulder"][arm], lower_start, z_deg=sign * 88, interp='BEZIER')
    settle_neutral(rig, end, interp='BEZIER')


def head_turn(rig, start, end, angle_deg=38, hold=True):
    """Turn the head to the side and back (rotation about the vertical axis;
    the flat face foreshortens, which reads as a turn)."""
    out_end = start + (end - start) // 3
    back_start = end - (end - start) // 3
    _rot(rig["head_pivot"], start, y_deg=0, interp='BEZIER')
    _rot(rig["head_pivot"], out_end, y_deg=angle_deg, interp='BEZIER')
    if hold:
        _rot(rig["head_pivot"], back_start, y_deg=angle_deg, interp='BEZIER')
    _rot(rig["head_pivot"], end, y_deg=0, interp='BEZIER')


def idle(rig, start, end, cycles=2):
    """Subtle standing idle: breathing (torso scale), tiny arm sway, small
    head tilt. Safe to layer over a neutral pose between actions."""
    span = end - start
    n_keys = cycles * 4
    for i in range(n_keys + 1):
        f = start + span * i / n_keys
        ph = (i % 4) / 4.0
        breathe = 1.0 + 0.02 * math.sin(2 * math.pi * ph)
        sway = 3.0 * math.sin(2 * math.pi * ph)
        _key(rig["torso"], "scale", 0, round(f), breathe, 'BEZIER')
        _key(rig["torso"], "scale", 1, round(f), breathe, 'BEZIER')
        _rot(rig["shoulder"]["L"], round(f), z_deg=sway, interp='BEZIER')
        _rot(rig["shoulder"]["R"], round(f), z_deg=-sway, interp='BEZIER')
        _rot(rig["head_pivot"], round(f), z_deg=1.5 * math.sin(2 * math.pi * ph),
             interp='BEZIER')


def add_billboard(rig, camera):
    """Make the character always face `camera` (Damped Track on the placement
    empty; the character plane's normal is placement-local -Y). Re-point at
    another camera by setting rig['billboard'].target = other_camera."""
    c = rig["placement"].constraints.new(type='DAMPED_TRACK')
    c.target = camera
    c.track_axis = 'TRACK_NEGATIVE_Y'
    rig["billboard"] = c
    return c


def place(rig, location=None, facing_deg=None):
    """Move / re-face a character after creation."""
    if location is not None:
        rig["placement"].location = location
    if facing_deg is not None:
        rig["placement"].rotation_euler = (0, 0, math.radians(180.0 + facing_deg))
