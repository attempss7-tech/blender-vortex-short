# props.py — own-built 3D objects for the V1 vortex short.
# Everything is built from primitives/curves in code; no downloaded models.
# Planes face +X (forward). The wing-lab wing spans X, chord along Y,
# airflow travels from -Y (leading edge) to +Y (trailing edge).
import math

import bpy

import common as cm

# ---------------------------------------------------------------- palette

SILVER = "#c9ced4"
SILVER_DARK = "#9aa0a8"
RUST = "#8a5a30"
DARK = "#2a2e33"
GLASS = "#20303c"
WHITE = "#eef1f4"
TEAL = "#1a7a8a"
ORANGE = "#e07830"
FLOW_CYAN = "#35b6e8"
VORTEX_CYAN = "#7ad8f0"
LIFT_GREEN = "#3ecf6a"
DEFECT_RED = "#e03030"
CONCRETE = "#9a958c"
WALL_WARM = "#b0a898"
GRASS = "#5a8a3e"
ASPHALT = "#4a4a52"
CLOUD = "#f4f8fc"
WOOD = "#8a6a42"


# ---------------------------------------------------------------- curves

def _curve_obj(name, mat, bevel=0.02):
    cu = bpy.data.curves.new(name + "_data", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = bevel
    cu.bevel_resolution = 2
    cu.materials.append(mat)
    obj = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(obj)
    return obj, cu


def airflow_line(name, parent, loc, length=4.8, arc=0.25, bevel=0.022):
    """One airflow line: a gently arched curve, local +Y = flow direction.
    Returns (pivot_empty, curve_obj). Pivot at the leading end; rotating
    the pivot about X lifts the tail off the surface (peel) or presses it
    down (glue). Points are LOCAL to the pivot."""
    pivot = cm.new_empty(name + "_Pivot", parent, loc)
    obj, cu = _curve_obj(name, cm.emissive_mat("M_Flow", FLOW_CYAN, 0.6),
                         bevel)
    obj.parent = pivot
    sp = cu.splines.new("BEZIER")
    n = 6
    sp.bezier_points.add(n - 1)
    for i in range(n):
        u = i / (n - 1)
        bp = sp.bezier_points[i]
        bp.co = (0.0, u * length, arc * math.sin(math.pi * u))
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"
    return pivot, obj


def flow_marker(name, pivot, length=4.8, arc=0.25):
    """Small cone that travels along an airflow line (parented to the pivot
    so it follows the line's tilt). Animate local Y 0..length."""
    m = cm.add_cone(name, 0.055, 0.005, 0.22,
                    cm.emissive_mat("M_FlowTip", "#bfeaff", 1.2),
                    parent=pivot, loc=(0, 0, 0),
                    rot=(-math.pi / 2, 0, 0))
    return m


def marker_z(y, length=4.8, arc=0.25):
    return arc * math.sin(math.pi * y / length)


def vortex_helix(name, parent, loc, length=1.8, r0=0.20, r1=0.05, turns=3.0):
    """A spiral tube (helix) whose axis is local +Y. Returns the spinner
    empty; rotating the spinner about Y spins the helix around its axis."""
    spin = cm.new_empty(name + "_Spin", parent, loc)
    obj, cu = _curve_obj(name, cm.emissive_mat("M_Vortex", VORTEX_CYAN, 0.8),
                         0.018)
    obj.parent = spin
    sp = cu.splines.new("POLY")
    n = 48
    sp.points.add(n - 1)
    for i in range(n):
        u = i / (n - 1)
        r = r0 + (r1 - r0) * u
        a = u * turns * 2 * math.pi
        sp.points[i].co = (r * math.cos(a), u * length, r * math.sin(a), 1.0)
    return spin


def fin(name, parent, loc, yaw_deg=20, size=1.0):
    """One vortex-generator fin: a thin angled wedge on a wing surface."""
    return cm.add_box(name, (0.10 * size, 0.025 * size, 0.15 * size),
                      cm.flat_mat("M_Fin", SILVER_DARK, 0.55),
                      parent=parent, loc=loc,
                      rot=(0, 0, math.radians(yaw_deg)))


# ---------------------------------------------------------------- wing lab

def build_wing_lab():
    """The big wing section at (-60, 0, 20) used by S3/S6/S7/S9.
    Returns a dict of the rig parts."""
    root = cm.new_empty("WingLab", loc=(-60, 0, 20))
    m_silver = cm.flat_mat("M_WingSilver", SILVER, 0.55)
    cm.add_box("WingLab_Wing", (7.0, 4.0, 0.22), m_silver, parent=root)
    # rounded leading edge (cylinder along X at y=-2)
    cm.add_cylinder("WingLab_LE", 0.11, 7.0, m_silver, parent=root,
                    loc=(0, -2.0, 0), rot=(0, math.pi / 2, 0))
    # support strut dropping out of frame
    cm.add_cylinder("WingLab_Strut", 0.09, 7.0,
                    cm.flat_mat("M_Strut", "#6a6e74"), parent=root,
                    loc=(0, 0, -3.6))
    # darker panel strips on top (reads as wing panels)
    m_panel = cm.flat_mat("M_WingPanel", "#b4b9c0", 0.6)
    for x in (-2.0, 0.0, 2.0):
        cm.add_box("WingLab_Panel%+d" % int(x), (0.06, 3.9, 0.02), m_panel,
                   parent=root, loc=(x, 0, 0.12))

    # ---- airflow lines (5, shared by S3/S6/S7; pivots keyed per shot).
    # Grouped under lines_root so S9's fin macro can hide them.
    lines_root = cm.new_empty("WingLab_FlowLines", parent=root)
    lines = []
    for i, x in enumerate((-2.8, -1.4, 0.0, 1.4, 2.8)):
        piv, _obj = airflow_line("Flow%d" % i, lines_root, (x, -2.4, 0.30))
        mk = flow_marker("FlowMark%d" % i, piv)
        lines.append(dict(pivot=piv, marker=mk, x=x))

    # ---- fin/bump row (visible S6/S7/S9; the "bumps" and the fins).
    # size 1.4 so the bumps read at the ~12 m wing-lab camera distance.
    fins_root = cm.new_empty("WingLab_Fins", parent=root, loc=(0, 0, 0.11))
    fins = []
    for i in range(12):
        x = -3.1 + i * 0.56
        fins.append(fin("VGFin%02d" % i, fins_root, (x, -1.4, 0.105),
                        yaw_deg=20 if i % 2 == 0 else -20, size=1.4))

    # ---- vortices (visible S7 only)
    vort_root = cm.new_empty("WingLab_Vortices", parent=root,
                             loc=(0, 0, 0.35))
    vortices = []
    for i, x in enumerate((-2.8, -1.4, 0.0, 1.4, 2.8)):
        vortices.append(vortex_helix("Vortex%d" % i, vort_root,
                                     (x, -0.9, 0.0)))

    # ---- lift arrow (visible S3 only)
    arrow = cm.new_empty("LiftArrow", parent=root, loc=(0, 0, 2.4))
    m_lift = cm.emissive_mat("M_Lift", LIFT_GREEN, 1.5)
    cm.add_cylinder("LiftArrow_Shaft", 0.07, 1.3, m_lift, parent=arrow,
                    loc=(0, 0, -0.3))
    cm.add_cone("LiftArrow_Head", 0.26, 0.01, 0.55, m_lift, parent=arrow,
                loc=(0, 0, 0.6))

    # ---- gleam bar for S9 (sweeps along the fin row)
    gleam = cm.add_box("FinGleam", (0.5, 0.06, 0.06),
                       cm.emissive_mat("M_Gleam", "#ffffff", 3.0),
                       parent=root, loc=(-3.2, -1.4, 0.30))

    return dict(root=root, lines_root=lines_root, lines=lines,
                fins_root=fins_root, fins=fins,
                vort_root=vort_root, vortices=vortices, arrow=arrow,
                gleam=gleam)


# ---------------------------------------------------------------- jets

def build_jet(name, loc, battered=False, scale=1.0):
    """Early jet prototype, forward = +X. Returns dict(root, burrs, ...).
    Burrs (battered only) are cones along both wing leading edges."""
    root = cm.new_empty(name, loc=loc)
    root.scale = (scale, scale, scale)
    m_body = cm.flat_mat("M_JetSilver", SILVER, 0.5)
    m_dark = cm.flat_mat("M_JetDark", DARK, 0.8)
    m_glass = cm.flat_mat("M_Glass", GLASS, 0.25)

    # fuselage along X
    cm.add_cylinder(name + "_Fuselage", 0.55, 7.0, m_body, parent=root,
                    rot=(0, math.pi / 2, 0))
    cm.add_cone(name + "_Nose", 0.55, 0.06, 1.3, m_body, parent=root,
                loc=(4.1, 0, 0), rot=(0, math.pi / 2, 0))
    cm.add_cone(name + "_TailCone", 0.50, 0.15, 1.1, m_body, parent=root,
                loc=(-4.0, 0, 0), rot=(0, -math.pi / 2, 0))
    cm.add_cylinder(name + "_Intake", 0.30, 0.12, m_dark, parent=root,
                    loc=(4.78, 0, 0), rot=(0, math.pi / 2, 0))
    cm.add_cylinder(name + "_Exhaust", 0.20, 0.12, m_dark, parent=root,
                    loc=(-4.58, 0, 0), rot=(0, math.pi / 2, 0))
    # canopy
    cm.add_sphere(name + "_Canopy", 0.5, m_glass, parent=root,
                  loc=(1.8, 0, 0.55), scale=(1.6, 0.8, 0.7))
    # main wing (swept back 12 deg) + tail
    cm.add_box(name + "_Wing", (1.7, 7.0, 0.12), m_body, parent=root,
               loc=(-0.3, 0, -0.1), rot=(0, 0, math.radians(12)))
    cm.add_box(name + "_TailFin", (1.2, 0.12, 1.4), m_body, parent=root,
               loc=(-3.6, 0, 0.8))
    cm.add_box(name + "_TailPlane", (0.9, 3.2, 0.08), m_body, parent=root,
               loc=(-3.7, 0, 0.15))
    # wheels
    for wx, wy in ((2.5, 0.0), (-1.5, 0.9), (-1.5, -0.9)):
        cm.add_cylinder(name + "_Wheel%g_%g" % (wx, wy), 0.22, 0.14,
                        m_dark, parent=root, loc=(wx, wy, -0.62),
                        rot=(math.pi / 2, 0, 0))
    # red cheatline stripe along the fuselage
    cm.add_box(name + "_Stripe", (6.6, 0.06, 0.18),
               cm.flat_mat("M_JetStripe", "#a03028", 0.7), parent=root,
               loc=(0, 0.53, 0.08))
    cm.add_box(name + "_Stripe2", (6.6, 0.06, 0.18),
               cm.flat_mat("M_JetStripe", "#a03028", 0.7), parent=root,
               loc=(0, -0.53, 0.08))

    burrs = []
    if battered:
        m_rust = cm.flat_mat("M_Rust", RUST, 0.95)
        m_scuff = cm.flat_mat("M_Scuff", "#7a7e84", 0.9)
        # scuff patches + dents
        cm.add_box(name + "_Patch1", (1.1, 0.06, 0.5), m_rust, parent=root,
                   loc=(0.5, 0.54, 0.25))
        cm.add_box(name + "_Patch2", (0.9, 0.9, 0.04), m_scuff, parent=root,
                   loc=(-1.2, 1.6, 0.0), rot=(0, 0, math.radians(12)))
        cm.add_sphere(name + "_Dent1", 0.28, m_scuff, parent=root,
                      loc=(-2.2, -0.45, 0.35), scale=(1.4, 0.5, 0.6))
        # bent wingtip (left tip droops)
        cm.add_box(name + "_BentTip", (1.5, 0.8, 0.10), m_body, parent=root,
                   loc=(-1.35, -3.55, -0.28),
                   rot=(0.25, 0, math.radians(12)))
        # burrs along the NEAR wing's leading edge (leading edge after the
        # 12 deg sweep: x = 0.53 - 0.208*y_s, y = 0.177 + 0.978*y_s).
        # All 10 sit on the camera-side wing (y_s -3.2..+0.4): v3 put 5
        # on the far wing, where S4's camera could never see them pop.
        burr_root = cm.new_empty(name + "_Burrs", parent=root)
        m_burr = cm.flat_mat("M_Burr", "#8f959c", 0.4)
        for i in range(10):
            ys = -3.2 + i * 0.40
            bx = 0.53 - 0.208 * ys
            by = 0.177 + 0.978 * ys
            b = cm.add_cone("%s_Burr%02d" % (name, i), 0.035, 0.008, 0.14,
                            m_burr, parent=burr_root,
                            loc=(bx, by, 0.03),
                            rot=(math.radians((i * 37) % 20 - 10),
                                 math.radians((i * 53) % 16 - 8), 0))
            burrs.append(b)
    else:
        burr_root = None

    # S8 glued airflow lines on the wings (flat, attached).
    # Lines run chordwise: pivot rotated +90 deg about Z so local +Y
    # points -X (the trailing edge is at -X for a +X-facing plane).
    flow8 = []
    for i, ys in enumerate((-2.2, -1.2, 1.2, 2.2)):
        bx = 0.53 - 0.208 * ys
        by = 0.177 + 0.978 * ys
        piv, _o = airflow_line("%s_Flow8_%d" % (name, i), root,
                               (bx + 0.15, by, 0.02), length=1.7, arc=0.06,
                               bevel=0.022)
        piv.rotation_euler = (0, 0, math.radians(90))
        flow8.append(piv)
    # S8 vortices: orient empty (+90 deg Z) + spinner child, so the spin
    # keys on rotation.y stay clean (no mixed Euler axes).
    vort8 = []
    vort8_orient = []
    for i, ys in enumerate((-1.6, 1.6)):
        bx = 0.53 - 0.208 * ys
        by = 0.177 + 0.978 * ys
        orient = cm.new_empty("%s_Vort8Orient_%d" % (name, i), parent=root,
                              loc=(bx - 0.2, by, 0.12))
        orient.rotation_euler = (0, 0, math.radians(90))
        sp = vortex_helix("%s_Vort8_%d" % (name, i), orient,
                          (0, 0, 0), length=1.1, r0=0.16,
                          r1=0.05, turns=2.5)
        vort8.append(sp)
        vort8_orient.append(orient)
    flow8_root = cm.new_empty(name + "_Flow8Root", parent=root)
    for p in flow8:
        p.parent = flow8_root
    for o in vort8_orient:
        o.parent = flow8_root
    # NOTE: re-parenting keeps world transform via matrix_parent_inverse
    # only if set; the pivots were placed in root space and Flow8Root sits
    # at root origin with no transform, so local coords are unchanged.

    return dict(root=root, burrs=burrs, burr_root=burr_root,
                flow8_root=flow8_root, flow8=flow8, vort8=vort8)


# ---------------------------------------------------------------- airliner

def build_airliner(name, loc):
    """Modern airliner, forward = +X, with fin rows on both wings."""
    root = cm.new_empty(name, loc=loc)
    m_white = cm.flat_mat("M_AirWhite", WHITE, 0.45)
    m_teal = cm.flat_mat("M_AirTeal", TEAL, 0.6)
    m_dark = cm.flat_mat("M_JetDark", DARK, 0.8)
    m_glass = cm.flat_mat("M_Glass", GLASS, 0.25)

    cm.add_cylinder(name + "_Fuselage", 1.1, 14.0, m_white, parent=root,
                    rot=(0, math.pi / 2, 0))
    cm.add_cone(name + "_Nose", 1.1, 0.12, 2.4, m_white, parent=root,
                loc=(8.1, 0, 0), rot=(0, math.pi / 2, 0))
    cm.add_cone(name + "_TailCone", 1.0, 0.25, 2.0, m_white, parent=root,
                loc=(-7.9, 0, 0), rot=(0, -math.pi / 2, 0))
    # cockpit windows
    cm.add_box(name + "_Cockpit", (1.4, 1.7, 0.5), m_glass, parent=root,
               loc=(6.6, 0, 0.62))
    # window strips
    for s in (1, -1):
        cm.add_box(name + "_Windows%d" % s, (10.5, 0.06, 0.34), m_glass,
                   parent=root, loc=(-0.5, s * 1.07, 0.35))
    # teal belly stripe
    cm.add_box(name + "_BellyStripe", (13.5, 0.06, 0.3), m_teal,
               parent=root, loc=(0, 1.06, -0.45))
    cm.add_box(name + "_BellyStripe2", (13.5, 0.06, 0.3), m_teal,
               parent=root, loc=(0, -1.06, -0.45))
    # swept wings (18 deg) + winglets
    cm.add_box(name + "_Wing", (2.6, 17.0, 0.18), m_white, parent=root,
               loc=(-0.5, 0, -0.3), rot=(0, 0, math.radians(18)))
    for s in (1, -1):
        cm.add_box(name + "_Winglet%d" % s, (1.6, 0.12, 1.1), m_teal,
                   parent=root, loc=(-6.1, s * 8.15, 0.25),
                   rot=(0, 0, math.radians(18)))
    # tail
    cm.add_box(name + "_TailFin", (2.0, 0.18, 3.0), m_teal, parent=root,
               loc=(-7.5, 0, 1.9))
    cm.add_box(name + "_TailPlane", (1.4, 6.0, 0.12), m_white, parent=root,
               loc=(-7.8, 0, 0.3))
    # engines under the wings
    for s in (1, -1):
        cm.add_cylinder(name + "_Engine%d" % s, 0.72, 2.8, m_white,
                        parent=root, loc=(0.6, s * 3.6, -1.35),
                        rot=(0, math.pi / 2, 0))
        cm.add_cylinder(name + "_EngineIn%d" % s, 0.55, 0.12, m_dark,
                        parent=root, loc=(2.02, s * 3.6, -1.35),
                        rot=(0, math.pi / 2, 0))
    # fin rows on the wings (2 rows per wing; wing swept 18 deg, so a
    # local point (xl, yl) maps to x = xl*cos18 - yl*sin18 - 0.5,
    # y = xl*sin18 + yl*cos18, z = -0.2)
    fins_root = cm.new_empty(name + "_Fins", parent=root)
    cos18, sin18 = math.cos(math.radians(18)), math.sin(math.radians(18))
    n = 0
    for row_xl in (0.9, 0.2):
        for k in range(9):
            yl = -7.2 + k * 1.8
            if abs(yl) < 1.4:
                continue
            fx = row_xl * cos18 - yl * sin18 - 0.5
            fy = row_xl * sin18 + yl * cos18
            fin("%s_VG%02d" % (name, n), fins_root, (fx, fy, -0.12),
                yaw_deg=20 if n % 2 == 0 else -20, size=1.4)
            n += 1
    return dict(root=root, fins_root=fins_root, n_fins=n)


# ---------------------------------------------------------------- hangar set

def build_hangar():
    """Hangar interior at the origin (S1). Returns dict of animated bits."""
    m_floor = cm.flat_mat("M_HangarFloor", CONCRETE, 0.95)
    m_wall = cm.flat_mat("M_HangarWall", WALL_WARM, 0.95)
    m_door = cm.flat_mat("M_HangarDoor", "#7a7268", 0.9)
    m_wood = cm.flat_mat("M_Wood", WOOD, 0.9)
    m_silver = cm.flat_mat("M_WingSilver", SILVER, 0.55)

    cm.add_plane("HangarFloor", 26, m_floor, loc=(0, 0, 0))
    cm.add_box("HangarBackWall", (26, 0.3, 7), m_wall, loc=(0, -6, 3.5))
    cm.add_box("HangarWallL", (0.3, 13, 7), m_wall, loc=(-12, 0, 3.5))
    cm.add_box("HangarWallR", (0.3, 13, 7), m_wall, loc=(12, 0, 3.5))
    cm.add_box("HangarDoor", (8, 0.12, 4.6), m_door, loc=(0, -5.8, 2.3))
    for i, x in enumerate((-3.0, 0.0, 3.0)):
        cm.add_box("HangarDoorSlat%d" % i, (0.12, 0.06, 4.4),
                   cm.flat_mat("M_DoorSlat", "#5f574e"), loc=(x, -5.72, 2.3))
    # high windows (pale glow)
    m_win = cm.emissive_mat("M_HangarWin", "#cfe4f5", 0.7)
    for x in (-8.0, 8.0):
        cm.add_box("HangarWin%+d" % int(x), (3.0, 0.08, 1.4), m_win,
                   loc=(x, -5.8, 5.2))

    # wing on trestles (the defect wing) — 5 m span so the wing plus both
    # engineers fit the narrow 9:16 frame
    cm.add_box("DefectWing", (5.0, 1.8, 0.15), m_silver, loc=(0, 0, 1.05))
    cm.add_cylinder("DefectWing_LE", 0.075, 5.0, m_silver,
                    loc=(0, -0.9, 1.05), rot=(0, math.pi / 2, 0))
    for x in (-1.7, 1.7):
        cm.add_box("Trestle%g" % x, (0.18, 1.3, 1.0), m_wood,
                   loc=(x, 0, 0.5))
        cm.add_box("TrestleFoot%g" % x, (0.5, 1.5, 0.08), m_wood,
                   loc=(x, 0, 0.04))
    # the defect: glowing red patch on the wing (pulses, then smoothed away)
    defect = cm.add_box("DefectPatch", (0.55, 0.45, 0.04),
                        cm.emissive_mat("M_Defect", DEFECT_RED, 1.6),
                        loc=(-1.0, 0.3, 1.15))

    # workbench + tools + model plane
    cm.add_box("BenchTop", (2.4, 0.9, 0.12), m_wood, loc=(3.2, -2.4, 0.95))
    for dx, dy in ((-1.0, -0.3), (1.0, -0.3), (-1.0, 0.3), (1.0, 0.3)):
        cm.add_box("BenchLeg%g%g" % (dx, dy), (0.1, 0.1, 0.9), m_wood,
                   loc=(3.2 + dx, -2.4 + dy, 0.45))
    cm.add_box("BenchTool1", (0.5, 0.12, 0.08),
               cm.flat_mat("M_Tool", "#3a3e44"), loc=(2.6, -2.5, 1.05))
    cm.add_cylinder("BenchTool2", 0.07, 0.4,
                    cm.flat_mat("M_Tool", "#3a3e44"), loc=(3.9, -2.3, 1.08),
                    rot=(0, math.pi / 2, 0))
    model = build_jet("ModelPlane", (3.2, -2.4, 1.15), scale=0.22)

    # calendar pinned to the hangar door (pages flip = time passing).
    # At x=-2.0 it sits in the narrow 9:16 frame (v1 at x=-4.6/-3.2 was
    # outside it) and clear of the door slats at x=-3/0/+3.
    cm.add_box("CalendarBoard", (1.2, 0.06, 1.5),
               cm.flat_mat("M_CalBoard", "#4a4038"), loc=(-2.0, -5.68, 3.1))
    pages = []
    for i, col in enumerate(("#e8dcc0", "#d8c8a8")):
        piv = cm.new_empty("CalPage%d_Pivot" % i, loc=(-2.0, -5.62, 3.75))
        pg = cm.add_plane("CalPage%d" % i, 1.0,
                          cm.flat_mat("M_CalPage%d" % i, col),
                          parent=piv, loc=(0, 0, -0.32),
                          rot=(math.radians(90), 0, 0))
        pg.scale = (0.95, 0.62, 1.0)
        pages.append(piv)

    # sanding dust puffs near the wing edge
    dust = []
    m_dust = cm.flat_mat("M_Dust", "#ddd4c0", 1.0)
    for i in range(6):
        dust.append(cm.add_sphere("Dust%d" % i, 0.035, m_dust,
                                  loc=(-1.0 + (i % 3) * 0.25,
                                       0.5 + (i // 3) * 0.2, 1.2)))

    # crates + barrel dressing
    cm.add_box("Crate1", (0.9, 0.9, 0.9), m_wood, loc=(-5.5, -4.5, 0.45))
    cm.add_box("Crate2", (0.7, 0.7, 0.7), m_wood, loc=(-4.7, -4.6, 0.35))
    cm.add_cylinder("Barrel1", 0.35, 0.9,
                    cm.flat_mat("M_Barrel", "#5a6a7a"),
                    loc=(5.6, -4.8, 0.45))
    return dict(defect=defect, model=model, pages=pages, dust=dust)


# ---------------------------------------------------------------- airfield

def build_airfield():
    """1940s airfield at x=+60 (S2/S4)."""
    m_grass = cm.flat_mat("M_Grass", GRASS, 1.0)
    m_asph = cm.flat_mat("M_Asphalt", ASPHALT, 0.95)
    m_white = cm.flat_mat("M_Marking", "#e8e8e0", 0.9)

    cm.add_plane("AirfieldGround", 1, m_grass, loc=(60, 0, -0.01))
    bpy.data.objects["AirfieldGround"].scale = (90, 50, 1)
    cm.add_box("Runway", (70, 6, 0.05), m_asph, loc=(60, 0, 0.02))
    for i in range(12):
        cm.add_box("RunwayMark%02d" % i, (1.6, 0.35, 0.02), m_white,
                   loc=(30 + i * 5.5, 0, 0.06))
    # windsock
    cm.add_cylinder("WindsockPole", 0.06, 4.0,
                    cm.flat_mat("M_Pole", "#8a8e94"), loc=(46, -6, 2.0))
    sock = cm.add_cone("Windsock", 0.28, 0.12, 1.4,
                       cm.flat_mat("M_Sock", ORANGE), loc=(46.7, -6, 3.8),
                       rot=(0, math.pi / 2, 0))
    # hangar silhouette in the background
    cm.add_box("FieldHangar", (10, 8, 4.5),
               cm.flat_mat("M_FieldHangar", "#8a7a66"),
               loc=(88, 14, 2.25))
    cm.add_box("FieldHangarRoof", (10.6, 8.6, 0.25),
               cm.flat_mat("M_FieldRoof", "#6a5a48"),
               loc=(88, 14, 4.6))
    # cones along the runway edge
    m_cone = cm.flat_mat("M_Cone", ORANGE)
    for i, x in enumerate((40, 52, 68, 80)):
        cm.add_cone("Cone%d" % i, 0.22, 0.05, 0.55, m_cone,
                    loc=(x, 4.2, 0.28))
    return dict(sock=sock)


# ---------------------------------------------------------------- clouds

def cloud(name, loc, scale=1.0):
    """One puffy cloud: a cluster of squashed spheres."""
    root = cm.new_empty(name, loc=loc)
    m = cm.flat_mat("M_Cloud", CLOUD, 1.0)
    puffs = [(0, 0, 0, 1.6), (1.4, 0.3, 0.15, 1.2), (-1.3, -0.2, 0.1, 1.1),
             (0.4, -0.6, -0.1, 1.0), (-0.5, 0.6, 0.2, 0.9)]
    for i, (dx, dy, dz, r) in enumerate(puffs):
        cm.add_sphere("%s_P%d" % (name, i), r, m, parent=root,
                      loc=(dx, dy, dz), scale=(1.3, 1.0, 0.5), seg=14,
                      rings=10)
    root.scale = (scale, scale, scale)
    return root


def build_clouds():
    """Cloud field near the sky sets (slow drift keyed in build_all)."""
    spots = [
        ("CloudA", (-75, 12, 13), 1.2), ("CloudB", (-44, -14, 26), 1.0),
        ("CloudC", (-60, 12, 26), 1.4), ("CloudD", (-48, 8, 18), 0.9),
        ("CloudE", (55, 18, 18), 1.3), ("CloudF", (48, 12, 26), 1.1),
        ("CloudG", (70, -14, 24), 1.2), ("CloudH", (85, 8, 28), 1.4),
        ("CloudI", (20, 10, 16), 0.9), ("CloudJ", (58, -6, 30), 1.0),
    ]
    return [cloud(n, loc, s) for n, loc, s in spots]
