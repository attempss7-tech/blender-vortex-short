#!/usr/bin/env python3
"""Render driver for the Blender vortex short (used by the Colab notebook).

Renders a frame range (or a list of test frames) from the .blend with
per-frame timing, printing a JSON summary. Supports resume: frames that
already exist in the output dir are skipped, and the missing frames are
rendered in contiguous blocks.

Usage (Colab):
  python3 scripts/colab_render.py --blender /content/blender/blender \
      --blend scenes/vortex.blend --out /content/frames \
      --start 0 --end 569
  python3 scripts/colab_render.py --blender ... --blend ... --out ... \
      --frames 122,200,490,622,853,1098,1200,1360,1560,1720,1800,2030,2270
  python3 scripts/colab_render.py --blender ... --gpu-probe

Local test (no GPU — Workbench stills only):
  python3 scripts/colab_render.py --blender ./tools/blender-4.2.23-linux-x64/blender \
      --blend scenes/vortex.blend --out /tmp/test_frames \
      --frames 122,1098 --engine BLENDER_WORKBENCH --scale 50
"""
import argparse
import json
import os
import re
import subprocess
import sys

SAVED_RE = re.compile(r"Saved:\s+'.*f(\d+)\.(?:png|jpg|jpeg)'\s+Time:\s+(\d+):(\d+\.\d+)")


def parse_args():
    p = argparse.ArgumentParser(description="Render vortex.blend frames with timing.")
    p.add_argument("--blender", required=True, help="Path to the blender binary.")
    p.add_argument("--blend", help="Path to the .blend file (not needed for --gpu-probe).")
    p.add_argument("--out", help="Output directory for frames (f####.png).")
    p.add_argument("--start", type=int, help="First frame of a range render.")
    p.add_argument("--end", type=int, help="Last frame of a range render.")
    p.add_argument("--frames", help="Comma-separated frame list (test frames).")
    p.add_argument("--engine", help="Override render engine (e.g. BLENDER_WORKBENCH for local tests).")
    p.add_argument("--scale", type=int, default=100, help="Resolution percentage (default 100).")
    p.add_argument("--gpu-probe", action="store_true", help="Print GPU info and exit.")
    return p.parse_args()


def run_blender(blender, args, what):
    """Run Blender, stream its output, return (exit_code, full_output)."""
    cmd = [blender, "-b"] + args
    print(f"+ {' '.join(cmd)}", flush=True)
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, bufsize=1)
    lines = []
    for line in proc.stdout:
        lines.append(line)
        # Stream progress lines so a long render doesn't look dead.
        if "Saved:" in line or "Fra:" in line or "Error" in line or "error" in line:
            print(line.rstrip(), flush=True)
    proc.wait()
    out = "".join(lines)
    if proc.returncode != 0:
        print(f"!! Blender failed ({what}), exit {proc.returncode}. Last 30 lines:", flush=True)
        print("\n".join(lines[-30:]), flush=True)
    return proc.returncode, out


def gpu_probe(blender):
    expr = (
        "import gpu\n"
        "try:\n"
        "    print('GPU_VENDOR', gpu.platform.vendor_get())\n"
        "    print('GPU_RENDERER', gpu.platform.renderer_get())\n"
        "    print('GPU_VERSION', gpu.platform.version_get())\n"
        "except Exception as e:\n"
        "    print('GPU_PROBE_UNAVAILABLE', e)\n"
    )
    code, out = run_blender(blender, ["--python-expr", expr], "gpu-probe")
    for line in out.splitlines():
        if line.startswith(("GPU_VENDOR", "GPU_RENDERER", "GPU_VERSION", "GPU_PROBE_UNAVAILABLE")):
            print(line, flush=True)
    return 0


def contiguous_blocks(frames):
    """Group sorted frame numbers into contiguous [start, end] blocks."""
    blocks = []
    for f in sorted(frames):
        if blocks and f == blocks[-1][1] + 1:
            blocks[-1][1] = f
        else:
            blocks.append([f, f])
    return blocks


def render_frames(args, frames):
    """Render the given frames (list), skipping ones already in --out."""
    os.makedirs(args.out, exist_ok=True)
    missing = [f for f in frames
               if not os.path.exists(os.path.join(args.out, f"f{f:04d}.png"))]
    already = len(frames) - len(missing)
    if already:
        print(f"Resume: {already} frame(s) already exist, skipping.", flush=True)
    if not missing:
        print("All requested frames already exist — nothing to render.", flush=True)
        return {}, []
    times = {}
    failed = []
    expr_parts = ["import bpy",
                  "bpy.context.scene.render.image_settings.file_format='PNG'"]
    if args.engine:
        expr_parts.append(f"bpy.context.scene.render.engine='{args.engine}'")
    if args.scale != 100:
        expr_parts.append(f"bpy.context.scene.render.resolution_percentage={args.scale}")
    expr = "; ".join(expr_parts)
    out_pattern = os.path.join(args.out, "f####")
    for start, end in contiguous_blocks(missing):
        if start == end:
            frame_args = ["-f", str(start)]
        else:
            frame_args = ["-s", str(start), "-e", str(end), "-a"]
        code, out = run_blender(
            args.blender,
            [args.blend, "--python-expr", expr, "-o", out_pattern, "-F", "PNG"] + frame_args,
            f"frames {start}-{end}")
        for m in SAVED_RE.finditer(out):
            fnum = int(m.group(1))
            times[fnum] = int(m.group(2)) * 60 + float(m.group(3))
        if code != 0:
            failed.extend(range(start, end + 1))
    return times, failed


def main():
    args = parse_args()
    if args.gpu_probe:
        return gpu_probe(args.blender)
    if not args.blend or not args.out:
        print("error: --blend and --out are required (unless --gpu-probe)", file=sys.stderr)
        return 2
    if args.frames:
        frames = [int(x) for x in args.frames.split(",") if x.strip()]
    elif args.start is not None and args.end is not None:
        frames = list(range(args.start, args.end + 1))
    else:
        print("error: give --frames LIST or --start/--end", file=sys.stderr)
        return 2
    times, failed = render_frames(args, frames)
    rendered = sorted(times)
    total = sum(times.values())
    summary = {
        "requested": len(frames),
        "rendered": len(rendered),
        "failed": sorted(set(failed)),
        "total_seconds": round(total, 1),
        "avg_seconds_per_frame": round(total / len(rendered), 2) if rendered else None,
        "min_seconds": round(min(times.values()), 2) if rendered else None,
        "max_seconds": round(max(times.values()), 2) if rendered else None,
        "frames_per_hour_at_avg": round(3600 / (total / len(rendered))) if rendered and total else None,
    }
    print("SUMMARY " + json.dumps(summary), flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
