# shots.py — the 10 shots of the V1 vortex short.
# Every shot function takes ctx (from build_all) and returns
# dict(cameras=[(marker_frame, cam)]). Frame ranges and word anchors come
# from SHOT_PLAN.md / voice/words.json. Camera keys span [start, end-1]
# (chicken convention); end is the exclusive shot boundary.
import importlib.util
import math
import os

import common as cm
import props

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

PI = math.pi


# ---------------------------------------------------------------- helpers

def pivot_x(pivot, frame, deg):
    pivot.rotation_euler[0] = math.radians(deg)
    pivot.keyframe_insert(data_path="rotation_euler", index=0, frame=frame)


def marker_run(marker, f_start, f_end, period=16, length=4.8, arc=0.25):
    """Flow marker travels 0..length along its line, repeatedly."""
    f = f_start
    while f < f_end:
        f1 = min(f + period, f_end)
        marker.location = (0, 0, 0)
        cm.kf(marker, f, "location")
        y = length * (f1 - f) / period
        marker.location = (0, y, props.marker_z(y, length, arc))
        cm.kf(marker, f1, "location")
        f = f1
    cm.set_linear_range(marker, f_start, f_end)


def spin(spinner, f_start, f_end, turns):
    spinner.rotation_euler = (0, 0, 0)
    cm.kf(spinner, f_start)
    spinner.rotation_euler = (0, turns * 2 * PI, 0)
    cm.kf(spinner, f_end)
    cm.set_linear_range(spinner, f_start, f_end)


def jet_pose(jet, frame, loc, roll_deg=0.0, pitch_deg=0.0, yaw_deg=0.0):
    """Keyframe a jet root's location + rotation (pitch: negative = nose
    up, for a +X-facing plane)."""
    cm.loc_key(jet["root"], frame, loc)
    cm.rot_key(jet["root"], frame,
               (math.radians(roll_deg), math.radians(pitch_deg),
                math.radians(yaw_deg)))


def sand_arm(rig, f_start, f_end, period=15):
    """Sanding: R arm out to the side, sawing up-down."""
    cm.joint_rot(rig["shoulder"]["R"], f_start, z_deg=-75, interp="BEZIER")
    cm.joint_rot(rig["elbow"]["R"], f_start, z_deg=-12, interp="BEZIER")
    f, i = f_start, 0
    while f <= f_end:
        ang = -75 + (12 if i % 2 == 0 else -12)
        cm.joint_rot(rig["shoulder"]["R"], f, z_deg=ang, interp="LINEAR")
        cm.joint_rot(rig["torso"], f, z_deg=2 if i % 2 == 0 else -2,
                     interp="LINEAR")
        f += max(2, period // 2)
        i += 1
    cm.joint_rot(rig["shoulder"]["R"], f_end, z_deg=-75, interp="BEZIER")


def raise_up(rig, arm, f_start, f_end):
    """Raise one arm straight up, hold, lower."""
    sign = -1 if arm == "R" else 1
    up, down = f_start + 6, f_end - 6
    cm.joint_rot(rig["shoulder"][arm], up, z_deg=sign * 150,
                 interp="BEZIER")
    cm.joint_rot(rig["elbow"][arm], up, z_deg=sign * -12, interp="BEZIER")
    cm.joint_rot(rig["shoulder"][arm], down, z_deg=sign * 150,
                 interp="BEZIER")
    cm.joint_rot(rig["elbow"][arm], down, z_deg=sign * -12,
                 interp="BEZIER")
    cm.joint_rot(rig["shoulder"][arm], f_end, z_deg=0, interp="BEZIER")
    cm.joint_rot(rig["elbow"][arm], f_end, z_deg=0, interp="BEZIER")


def look_up(rig, f_start, f_end, deg=-20):
    """Head pitch up (negative local X = face tilts up)."""
    cm.joint_rot(rig["head_pivot"], f_start, x_deg=0, interp="BEZIER")
    cm.joint_rot(rig["head_pivot"], f_start + 8, x_deg=deg, interp="BEZIER")
    cm.joint_rot(rig["head_pivot"], f_end - 4, x_deg=deg, interp="BEZIER")
    cm.joint_rot(rig["head_pivot"], f_end, x_deg=0, interp="BEZIER")


def look_down(rig, f_start, f_end, deg=15):
    cm.joint_rot(rig["head_pivot"], f_start, x_deg=0, interp="BEZIER")
    cm.joint_rot(rig["head_pivot"], f_start + 8, x_deg=deg, interp="BEZIER")
    cm.joint_rot(rig["head_pivot"], f_end - 4, x_deg=deg, interp="BEZIER")
    cm.joint_rot(rig["head_pivot"], f_end, x_deg=0, interp="BEZIER")


# ---------------------------------------------------------------- S1 hangar

def shot01(ctx):
    eng1, eng2 = ctx["eng1"], ctx["eng2"]
    hangar = ctx["hangar"]
    cam, _f = cm.build_shot_camera(
        "Cam01",
        [(0, (0.2, 11.8, 2.7), 35), (111, (-0.2, 10.2, 2.3), 37),
         (215, (0.5, 9.6, 3.8), 36)],
        [(0, (0, 0.5, 1.1)), (111, (0, 0.5, 1.1)),
         (215, (1.2, -0.5, 2.3))],
        0, 215)
    # staging: Eng1 right at the defect (x=-1.0) sanding, Eng2 watching.
    # Both stand well in front of the wing (y >= 1.6) so the wing slab
    # never cuts across them, and close together (x -1.4/+1.1) so both
    # fit the narrow 9:16 frame (v2 at -1.9/+1.5 put Eng2 out of frame).
    cm.place_rig(eng1, 0, (-1.4, 1.6, 0))
    cm.place_rig(eng1, 215, (-1.4, 1.6, 0))
    cm.face_camera(eng1, 0, (-1.4, 1.6), (0.2, 11.8))
    cm.face_camera(eng1, 215, (-1.4, 1.6), (0.5, 9.6))
    cm.place_rig(eng2, 0, (1.1, 1.9, 0))
    cm.place_rig(eng2, 215, (1.1, 1.9, 0))
    cm.face_camera(eng2, 0, (1.1, 1.9), (0.2, 11.8))
    cm.face_camera(eng2, 215, (1.1, 1.9), (0.5, 9.6))

    rig2d.settle_neutral(eng1, 0)
    rig2d.settle_neutral(eng2, 0)
    # sanding f9-111, looking down at the wing
    sand_arm(eng1, 9, 111)
    look_down(eng1, 9, 111)
    rig2d.idle(eng2, 0, 111, cycles=2)
    rig2d.head_turn(eng2, 40, 70, angle_deg=30)
    # "realized" f119-147: both stop and look up; Eng2 points up
    rig2d.settle_neutral(eng1, 119)
    rig2d.settle_neutral(eng2, 119)
    look_up(eng1, 119, 196)
    look_up(eng2, 119, 196)
    raise_up(eng2, "R", 119, 196)
    rig2d.settle_neutral(eng1, 215)
    rig2d.settle_neutral(eng2, 215)

    # defect patch: pulses while sanded, smoothed away by f111
    defect = hangar["defect"]
    cm.scale_at(defect, 0, 1.0)
    f = 9
    while f < 100:
        cm.scale_at(defect, f, 1.18)
        cm.scale_at(defect, min(f + 6, 100), 1.0)
        f += 12
    cm.scale_at(defect, 100, 1.0)
    cm.scale_at(defect, 111, cm.HIDDEN)
    cm.set_linear_range(defect, 100, 111)

    # calendar pages flip: f28-38 and f68-78 (time passing)
    for piv, fs in zip(hangar["pages"], (28, 68)):
        piv.rotation_euler = (0, 0, 0)
        cm.kf(piv, fs)
        piv.rotation_euler = (-2.6, 0, 0)
        cm.kf(piv, fs + 10)

    # sanding dust: staggered puffs drifting off the wing edge
    for i, d in enumerate(hangar["dust"]):
        fs = 15 + i * 12
        x0 = d.location.x
        y0, z0 = d.location.y, d.location.z
        cm.scale_at(d, 0, cm.HIDDEN)
        cm.scale_at(d, fs, cm.HIDDEN)
        cm.scale_at(d, fs + 3, 1.0)
        cm.loc_key(d, fs, (x0, y0, z0))
        cm.loc_key(d, fs + 25, (x0 + 0.35, y0 + 0.45, z0 + 0.18))
        cm.scale_at(d, fs + 25, cm.HIDDEN)
        cm.set_linear_range(d, fs, fs + 25)

    # model plane lifts off the bench f153-196 ("keeping planes in the air")
    model = hangar["model"]["root"]
    cm.loc_key(model, 0, (3.2, -2.4, 1.15))
    cm.rot_key(model, 0, (0, 0, 0))
    cm.loc_key(model, 150, (3.2, -2.4, 1.15))
    cm.rot_key(model, 150, (0, 0, 0))
    cm.loc_key(model, 196, (1.2, -0.5, 2.9))
    cm.rot_key(model, 196, (0.15, -0.45, 0.1))
    cm.loc_key(model, 215, (0.6, 0.2, 3.1))
    cm.rot_key(model, 215, (0.1, -0.4, 0.15))
    return dict(cameras=[(0, cam)])


# ---------------------------------------------------------------- S2 stall

def shot02(ctx):
    hero = ctx["hero"]
    s1, s2 = ctx["smooth1"], ctx["smooth2"]
    cam, _f = cm.build_shot_camera(
        "Cam02",
        [(216, (48, -26, 5), 28), (310, (56, -28, 6), 28),
         (353, (64, -27, 6.5), 28)],
        [(216, (50, 0, 0.8)), (310, (65.5, 0, 3.6)),
         (353, (74, 0, 2.6))],
        216, 353)
    # hero: taxi, lift off, pitch up, STALL + drop f303-318, low recovery
    jet_pose(hero, 216, (48, 0, 0.6))
    jet_pose(hero, 270, (58, 0, 1.2), pitch_deg=-5)
    jet_pose(hero, 296, (63, 0, 3.2), pitch_deg=-20)
    jet_pose(hero, 303, (64.5, 0, 4.2), pitch_deg=-29)
    # shudder f304-318: rapid pitch/roll jitter while dropping
    for k, f in enumerate(range(304, 319, 2)):
        sgn = 1 if k % 2 == 0 else -1
        z = 4.2 - (f - 303) * 0.11
        jet_pose(hero, f, (64.5 + (f - 303) * 0.1, 0, z),
                 roll_deg=sgn * 4, pitch_deg=-29 + sgn * 5)
    jet_pose(hero, 318, (66, 0, 2.6), pitch_deg=-9)
    jet_pose(hero, 330, (68.5, 0, 1.8), pitch_deg=-3)
    jet_pose(hero, 340, (71, 0, 2.3), pitch_deg=-4)
    jet_pose(hero, 347, (72.8, 0, 2.8), pitch_deg=-2)
    jet_pose(hero, 353, (75, 0, 2.6), pitch_deg=-3)
    # the other two prototypes: shallow climb + wobble, on the FAR side
    # (y +5/+9) and staggered behind the hero so they never overlap it
    for jet, x0, x1, y0, y1, z1 in ((s1, 46, 66, 5.0, 4.5, 3.2),
                                   (s2, 44, 62, 9.0, 8.5, 3.0)):
        jet_pose(jet, 216, (x0, y0, 0.7))
        f = 216
        i = 0
        while f <= 353:
            u = (f - 216) / 137.0
            jet_pose(jet, f, (x0 + (x1 - x0) * u, y0 + (y1 - y0) * u,
                              0.7 + (z1 - 0.7) * u),
                     roll_deg=6 if i % 2 == 0 else -6,
                     pitch_deg=-4 if i % 2 == 0 else -1)
            f += 18
            i += 1
        jet_pose(jet, 353, (x1, y1, z1), pitch_deg=-2)
    # windsock waves
    sock = ctx["airfield"]["sock"]
    for f, a in ((216, 0), (260, 8), (300, -6), (353, 4)):
        cm.rot_key(sock, f, (0, math.radians(90), math.radians(a)))
    return dict(cameras=[(216, cam)])


# ---------------------------------------------------------------- S3 peel

def shot03(ctx):
    wl = ctx["winglab"]
    cam, _f = cm.build_shot_camera(
        "Cam03",
        [(354, (-52, -11, 24.5), 36), (430, (-53, -10, 23.5), 40),
         (499, (-54, -9.5, 22.5), 40)],
        [(354, (-60, 0, 20.3)), (430, (-60, 0, 20.0)),
         (499, (-60, 0, 19.2))],
        354, 499)
    # wing holds, then SINKS as lift dies (f476-499)
    root = wl["root"]
    cm.loc_key(root, 354, (-60, 0, 20))
    cm.loc_key(root, 475, (-60, 0, 20))
    cm.loc_key(root, 499, (-60, 0, 18.2))
    cm.set_linear_range(root, 475, 499)
    # airflow: streaming, then PEELS OFF in sequence f360-410
    for i, ln in enumerate(wl["lines"]):
        piv = ln["pivot"]
        fs = 360 + i * 8
        pivot_x(piv, 354, 0)
        pivot_x(piv, fs, 0)
        pivot_x(piv, fs + 14, 37)
        pivot_x(piv, 499, 37)
        marker_run(ln["marker"], 354, 499, period=16)
    # lift arrow: bobs, then VANISHES f450-476 ("instantly killing lift")
    arrow = wl["arrow"]
    cm.scale_at(arrow, 353, cm.HIDDEN)
    cm.scale_at(arrow, 354, 1.0)
    for f in (374, 394, 414, 434):
        cm.scale_at(arrow, f, 1.08)
        cm.scale_at(arrow, f + 10, 1.0)
    cm.scale_at(arrow, 450, 1.0)
    cm.scale_at(arrow, 465, 0.35)
    cm.scale_at(arrow, 476, cm.HIDDEN)
    cm.scale_at(arrow, 499, cm.HIDDEN)
    cm.set_linear_range(arrow, 450, 476)
    return dict(cameras=[(354, cam)])


# ---------------------------------------------------------------- S4 burrs

def shot04(ctx):
    hero = ctx["hero"]
    # NOTE: no engineer in this shot — the v1 stills showed a person next
    # to the wing would either sit behind the camera or fill the frame at
    # this macro distance. The burrs popping ARE the action here.
    # The near wing spans world y -1.5..2 (jet at y=2); the camera glides
    # along exactly that range (v1 overshot to y=-3..+2 and missed it).
    cam, _f = cm.build_shot_camera(
        "Cam04",
        [(500, (66.5, -5.5, 2.0), 38), (585, (65.8, -2.5, 1.9), 40),
         (669, (65.0, 1.0, 2.1), 40)],
        [(500, (62.8, -1.0, 0.9)), (585, (62.8, 0.5, 0.9)),
         (669, (62.8, 2.2, 0.9))],
        500, 669)
    # hero jet parked on the airfield, nose into the light
    jet_pose(hero, 500, (62, 2, 0.6))
    jet_pose(hero, 669, (62, 2, 0.6))
    # burrs POP UP one by one along the wing edge f556-646
    for i, b in enumerate(hero["burrs"]):
        fp = 556 + i * 10
        cm.scale_at(b, 500, cm.HIDDEN)
        cm.scale_at(b, fp - 1, cm.HIDDEN)
        cm.scale_at(b, fp + 1, 1.25)
        cm.scale_at(b, fp + 4, 1.0)
        cm.scale_at(b, 669, 1.0)
    return dict(cameras=[(500, cam)])


# ---------------------------------------------------------------- S5 better

def shot05(ctx):
    hero = ctx["hero"]
    s1, s2 = ctx["smooth1"], ctx["smooth2"]
    cam, _f = cm.build_shot_camera(
        "Cam05",
        [(670, (22, -27, 24), 26), (777, (42, -27, 24.5), 26)],
        [(670, (30, 0, 22)), (777, (50, 0, 22))],
        670, 777)
    # hero flies STEADY and level; the smooth jets wobble behind it on
    # the far side (y +5/+6) so the three never overlap in frame. The
    # 26 mm lens keeps all three in the narrow 9:16 frame.
    jet_pose(hero, 670, (28, 0, 22), pitch_deg=-2)
    jet_pose(hero, 777, (52, 0, 22), pitch_deg=-2)
    for jet, x0, y, z in ((s1, 23, 5.0, 20.5), (s2, 22, 6.0, 23.5)):
        jet_pose(jet, 670, (x0, y, z), pitch_deg=-2)
        f, i = 670, 0
        while f <= 777:
            u = (f - 670) / 107.0
            jet_pose(jet, f, (x0 + 24 * u, y, z + 0.8 * math.sin(u * 9.0)),
                     roll_deg=9 if i % 2 == 0 else -9,
                     pitch_deg=-6 if i % 2 == 0 else 2)
            f += 12
            i += 1
        jet_pose(jet, 777, (x0 + 24, y, z), pitch_deg=-2)
    return dict(cameras=[(670, cam)])


# ---------------------------------------------------------------- S6 bend down

def shot06(ctx):
    wl = ctx["winglab"]
    cam, _f = cm.build_shot_camera(
        "Cam06",
        [(778, (-54, -10, 22.2), 36), (874, (-56, -8.5, 21.6), 40)],
        [(778, (-60, 0, 20.3)), (874, (-60, 0, 20.3))],
        778, 874)
    root = wl["root"]
    cm.loc_key(root, 778, (-60, 0, 20))
    cm.loc_key(root, 874, (-60, 0, 20))
    # airflow starts HIGH, then BENDS DOWN onto the surface f786-832
    for i, ln in enumerate(wl["lines"]):
        piv = ln["pivot"]
        fs = 786 + i * 8
        pivot_x(piv, 778, 31)
        pivot_x(piv, fs, 31)
        pivot_x(piv, fs + 14, 0)
        pivot_x(piv, 874, 0)
        marker_run(ln["marker"], 778, 874, period=16)
    return dict(cameras=[(778, cam)])


# ---------------------------------------------------------------- S7 vortices

def shot07(ctx):
    wl = ctx["winglab"]
    cam, _f = cm.build_shot_camera(
        "Cam07",
        [(875, (-54, -10.5, 23.5), 38), (970, (-57, -9, 22.5), 40)],
        [(875, (-59, 0, 20.4)), (970, (-61, 0, 20.4))],
        875, 970)
    root = wl["root"]
    cm.loc_key(root, 875, (-60, 0, 20))
    cm.loc_key(root, 970, (-60, 0, 20))
    # lines loose (+14 deg), then SNAP back onto the wing f922-933 (glued)
    for i, ln in enumerate(wl["lines"]):
        piv = ln["pivot"]
        fs = 922 + i * 2
        pivot_x(piv, 875, 14)
        pivot_x(piv, fs, 14)
        pivot_x(piv, fs + 8, 0)
        pivot_x(piv, 970, 0)
        marker_run(ln["marker"], 875, 970, period=16)
    # vortices APPEAR and SPIN f889-917, one behind each bump
    for i, sp in enumerate(wl["vortices"]):
        fs = 889 + i * 5
        cm.scale_at(sp, 875, cm.HIDDEN)
        cm.scale_at(sp, fs, cm.HIDDEN)
        cm.scale_at(sp, fs + 6, 1.0)
        cm.scale_at(sp, 970, 1.0)
        spin(sp, fs, 970, turns=4)
    return dict(cameras=[(875, cam)])


# ---------------------------------------------------------------- S8 climb

def shot08(ctx):
    hero = ctx["hero"]
    cam, _f = cm.build_shot_camera(
        "Cam08",
        [(971, (28, -18, 12), 30), (1016, (36, -20, 20), 30),
         (1031, (40, -20, 24), 30)],
        [(971, (38, 5, 18)), (1016, (48, 5, 28)), (1031, (51, 5, 31.5))],
        971, 1031)
    # STEEP CLIMB: pitch up hard f990-1016, rising ~13 m
    jet_pose(hero, 971, (38, 5, 18), pitch_deg=-2)
    jet_pose(hero, 990, (42, 5, 20.5), pitch_deg=-20)
    jet_pose(hero, 1016, (48, 5, 28), pitch_deg=-49)
    jet_pose(hero, 1031, (51, 5, 31.5), pitch_deg=-49)
    # glued airflow + spinning vortices on the wings
    for sp in hero["vort8"]:
        spin(sp, 971, 1031, turns=3)
    return dict(cameras=[(971, cam)])


# ---------------------------------------------------------------- S9 fins

def shot09(ctx):
    wl = ctx["winglab"]
    # ~6.8 m out (v1's 2.4 m macro showed a single fin as a grey slab with
    # no context); now ~4 fins of the row read with the wing surface.
    cam, _f = cm.build_shot_camera(
        "Cam09",
        [(1032, (-56.5, -6.5, 21.8), 40), (1099, (-63.5, -6.0, 21.6), 40)],
        [(1032, (-58.5, -1.4, 20.25)), (1099, (-61.5, -1.4, 20.25))],
        1032, 1099)
    root = wl["root"]
    cm.loc_key(root, 1032, (-60, 0, 20))
    cm.loc_key(root, 1099, (-60, 0, 20))
    # the name moment: a highlight sweep travels WITH the camera's focus
    # down the fin row f1053-1089 (v2 swept the full row and outran the
    # frame, so it was never visible)
    gleam = wl["gleam"]
    cm.loc_key(gleam, 1032, (1.2, -1.4, 0.30))
    cm.loc_key(gleam, 1053, (1.2, -1.4, 0.30))
    cm.loc_key(gleam, 1089, (-1.4, -1.4, 0.30))
    cm.loc_key(gleam, 1099, (-1.4, -1.4, 0.30))
    cm.set_linear_range(gleam, 1053, 1089)
    # fins pulse gently in sequence as the sweep passes
    for i, fobj in enumerate(wl["fins"]):
        fs = 1053 + i * 3
        cm.scale_at(fobj, 1032, 1.0)
        cm.scale_at(fobj, fs, 1.0)
        cm.scale_at(fobj, fs + 2, 1.18)
        cm.scale_at(fobj, fs + 5, 1.0)
        cm.scale_at(fobj, 1099, 1.0)
    return dict(cameras=[(1032, cam)])


# ---------------------------------------------------------------- S10 airliner

def shot10(ctx):
    air = ctx["airliner"]
    # starts close on the wing (fin rows read), then pulls back HARD so
    # the 18 m airliner fits whole with sky around it for the finale
    # (47 m out at 28 mm: the jet spans ~80% of the frame width)
    cam, _f = cm.build_shot_camera(
        "Cam10",
        [(1100, (48, -20, 27), 32), (1180, (58, -28, 29), 30),
         (1283, (70, -46, 33), 28)],
        [(1100, (50, 0, 26)), (1180, (60, 0, 26.2)),
         (1283, (76, 0, 26.5))],
        1100, 1283)
    root = air["root"]
    cm.loc_key(root, 1100, (48, 0, 26))
    cm.rot_key(root, 1100, (0, 0, 0))
    cm.loc_key(root, 1200, (63, 0, 26.2))
    cm.rot_key(root, 1200, (math.radians(7), 0, 0))
    cm.loc_key(root, 1283, (78, 0, 26.5))
    cm.rot_key(root, 1283, (0, 0, 0))
    return dict(cameras=[(1100, cam)])


SHOTS = [shot01, shot02, shot03, shot04, shot05,
         shot06, shot07, shot08, shot09, shot10]
