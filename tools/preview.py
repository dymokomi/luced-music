#!/usr/bin/env python3
"""Capture a real Metal frame of the window as a PNG, without the screen.

    tools/preview.py [--scene rack|patch|clip|curve|playing] [--output build/preview.png]

Uses luce-gpu's test observer to read the drawable back (luced-photo's way)."""
from pathlib import Path
import argparse, os, shutil, struct, subprocess, tempfile, zlib

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--scene", default="rack")
parser.add_argument("--output", type=Path, default=None)
arguments = parser.parse_args()
output = arguments.output or ROOT / f"build/preview-{arguments.scene}.png"


def chunk(tag, payload):
    return struct.pack(">I", len(payload)) + tag + payload + struct.pack(">I", zlib.crc32(tag + payload) & 0xffffffff)


if True:
    project = ROOT / "build/preview-project"
    shutil.rmtree(project, ignore_errors=True)
    project.mkdir(parents=True)
    shutil.copytree(ROOT / "src", project / "src")
    shutil.copy2(ROOT / "tools/preview.luc", project / "src/main.luc")
    native = (ROOT.parent / "luce-gpu/tests/gpu/native.lucb").read_text()
    (project / "src/probe.lucb").write_text(native + "\n" + (ROOT / "tools/readback.lucb").read_text())
    manifest = (ROOT / "package.prisma").read_text()
    for name in [line.split('"')[1] for line in manifest.splitlines() if line.strip().startswith("def dependency")]:
        manifest = manifest.replace(f'"../{name}"', f'"{ROOT.parent / name}"')
    (project / "package.prisma").write_text(manifest)
    binary = project / "preview"
    environment = dict(os.environ, LUCE_CACHE=str(ROOT / "build/cache"), LUCE_CRASH_WINDOW="0")
    subprocess.run([os.environ.get("LUCE") or shutil.which("luce"), "build", str(project / "src/main.luc"), "--native", "-o", str(binary)], check=True, env=environment, timeout=900)
    ppm = project / "preview.ppm"
    subprocess.run([str(binary), str(ppm), arguments.scene], check=True, timeout=120, env=environment)
    header, dimensions, maximum, pixels = ppm.read_bytes().split(b"\n", 3)
    width, height = map(int, dimensions.split())
    rows = b"".join(b"\0" + pixels[y * width * 3:(y + 1) * width * 3] for y in range(height))
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(rows, 9)) + chunk(b"IEND", b"")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(png)
    print(f"{output} ({width} × {height})")
