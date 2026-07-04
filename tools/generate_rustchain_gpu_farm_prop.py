from __future__ import annotations

import importlib.util
import math
import struct
import zlib
from pathlib import Path


WORK = Path(__file__).resolve().parent
BASE_PATH = WORK / "base_hash_crate.py"
if not BASE_PATH.exists():
    BASE_PATH = WORK / "generate_rustchain_hash_crate_prop.py"
ROOT = WORK / "out" if (WORK / "base_hash_crate.py").exists() else WORK.parent
PROP_NAME = "rustchain_gpu_farm"
OUT = ROOT / "pk3_build" / "models" / "props" / PROP_NAME

source = BASE_PATH.read_text(encoding="utf-8").replace("from PIL import Image, ImageDraw, ImageFont\n", "")
source = source.split("\ndef font")[0]
base_ns: dict[str, object] = {"__file__": str(BASE_PATH), "__name__": "base_hash_crate_stdlib"}
exec(compile(source, str(BASE_PATH), "exec"), base_ns)
ObjBuilder = base_ns["ObjBuilder"]
write_iqm_direct = base_ns["write_iqm_direct"]

MATERIALS = {
    "rig_frame": {
        "texture": "gpu_farm_frame.tga",
        "color": (38, 42, 48),
        "kd": (0.15, 0.16, 0.18),
    },
    "gpu_board": {
        "texture": "gpu_farm_boards.tga",
        "color": (31, 86, 79),
        "kd": (0.08, 0.34, 0.31),
    },
    "fan_glow": {
        "texture": "gpu_farm_fans.tga",
        "color": (40, 205, 218),
        "kd": (0.06, 0.70, 0.76),
    },
    "rtc_cable": {
        "texture": "gpu_farm_cables.tga",
        "color": (224, 135, 40),
        "kd": (0.85, 0.42, 0.10),
    },
}

README_TEXT = """# RustChain GPU Farm prop

Original low-poly static prop for the Xonotic RustChain Arena prop bounty #14015:
https://github.com/Scottcjn/rustchain-bounties/issues/14015

## Package

| File | Purpose |
| --- | --- |
| `rustchain_gpu_farm.iqm` | Static IQM model for a compact mining rig / GPU farm |
| `rustchain_gpu_farm_0.skin` | DarkPlaces/Xonotic material-to-texture mapping |
| `gpu_farm_frame.tga` | 256x256 dark rack frame texture |
| `gpu_farm_boards.tga` | 256x256 teal GPU board texture |
| `gpu_farm_fans.tga` | 256x256 cyan fan glow texture |
| `gpu_farm_cables.tga` | 256x256 orange cable texture |
| `rustchain_gpu_farm_preview.png` | Preview render with material swatches |
| `rustchain_gpu_farm_source.obj` | Editable source mesh |
| `rustchain_gpu_farm_source.mtl` | Source material table |

## Design

This model covers the **mining rig / GPU farm** wishlist item. It is a small
arena set-dressing prop with a two-tier metal rack, six visible GPU boards,
cyan fan hubs, orange power cables, and a raised RTC hash light bar. The shape
is intentionally compact so map authors can use it as cover, background tech,
or a cluster near a validator room.

The geometry and textures are procedural and original. No external meshes,
samples, texture packs, or AI model files are embedded.
"""

LICENSE_TEXT = """RustChain GPU Farm prop

Copyright 2026

This model, texture pack, preview image, and source mesh are licensed under
the Creative Commons Attribution-ShareAlike 4.0 International License
(CC-BY-SA-4.0).

License summary and legal code:
https://creativecommons.org/licenses/by-sa/4.0/
"""


def add_gpu(mesh, x: float, y: float, z: float, angle: float) -> None:
    # A board, rear bracket, twin fans, and small heat-pipe bar.
    mesh.add_box((x, y, z), (0.52, 0.055, 0.28), "gpu_board")
    mesh.add_box((x - 0.23, y - 0.035, z), (0.035, 0.09, 0.31), "rig_frame")
    for dx in (-0.13, 0.13):
        mesh.add_cylinder(
            (x + dx, y - 0.065, z + 0.01),
            radius=0.072,
            height=0.035,
            segments=16,
            side_material="fan_glow",
            cap_material="fan_glow",
            phase=angle,
        )
    mesh.add_box((x, y - 0.085, z + 0.11), (0.42, 0.035, 0.028), "rtc_cable")


def add_cable_arc(mesh, x0: float, x1: float, z: float, row_y: float) -> None:
    segments = 7
    last = None
    for i in range(segments + 1):
        t = i / segments
        x = x0 + (x1 - x0) * t
        y = row_y - 0.15 - math.sin(t * math.pi) * 0.11
        point = (x, y, z + math.sin(t * math.pi) * 0.05)
        if last is not None:
            mx = (last[0] + point[0]) / 2
            my = (last[1] + point[1]) / 2
            mz = (last[2] + point[2]) / 2
            length = math.dist(last, point)
            mesh.add_box((mx, my, mz), (length, 0.025, 0.025), "rtc_cable")
        last = point


def build_mesh():
    mesh = ObjBuilder()

    # Base tray and vertical rack rails.
    mesh.add_box((0, 0, 0.08), (1.72, 0.76, 0.12), "rig_frame")
    mesh.add_box((0, 0, 0.62), (1.72, 0.70, 0.08), "rig_frame")
    for x in (-0.78, 0.78):
        for y in (-0.31, 0.31):
            mesh.add_box((x, y, 0.35), (0.08, 0.08, 0.62), "rig_frame")

    # Back power rail and top RTC light bar.
    mesh.add_box((0, 0.36, 0.42), (1.55, 0.09, 0.20), "rig_frame")
    mesh.add_box((0, -0.39, 0.73), (1.24, 0.06, 0.08), "fan_glow")

    x_positions = (-0.52, 0.0, 0.52)
    for row, z in enumerate((0.34, 0.58)):
        for idx, x in enumerate(x_positions):
            add_gpu(mesh, x, -0.03, z, angle=(row + idx) * 0.35)
            add_cable_arc(mesh, x - 0.10, x + 0.10, z - 0.11, -0.03)

    # Small corner feet.
    for x in (-0.66, 0.66):
        for y in (-0.24, 0.24):
            mesh.add_box((x, y, -0.02), (0.22, 0.18, 0.08), "rig_frame")

    return mesh


def write_textures() -> None:
    for material, info in MATERIALS.items():
        pixels = [[info["color"] for _ in range(256)] for _ in range(256)]

        def set_pixel(x: int, y: int, color: tuple[int, int, int]) -> None:
            if 0 <= x < 256 and 0 <= y < 256:
                pixels[y][x] = color

        def line_diag(offset: int, color: tuple[int, int, int], width: int) -> None:
            for x in range(256):
                y = 255 - x + offset
                for w in range(-width, width + 1):
                    set_pixel(x, y + w, color)

        if material == "rig_frame":
            for i in range(0, 256, 32):
                for y in range(256):
                    for dx in range(-1, 2):
                        set_pixel(i + dx, y, (58, 64, 70))
                for x in range(256):
                    set_pixel(x, i, (21, 23, 26))
                    set_pixel(x, i + 1, (21, 23, 26))
        elif material == "gpu_board":
            for y in range(28, 230, 42):
                for yy in range(y, y + 8):
                    for x in range(18, 239):
                        set_pixel(x, yy, (64, 150, 135))
            for x in range(34, 230, 40):
                for yy in range(38, 221):
                    set_pixel(x, yy, (16, 52, 47))
                    set_pixel(x + 16, yy, (16, 52, 47))
                for xx in range(x, x + 17):
                    set_pixel(xx, 38, (16, 52, 47))
                    set_pixel(xx, 220, (16, 52, 47))
        elif material == "fan_glow":
            for y in range(256):
                for x in range(256):
                    dist = math.hypot(x - 128, y - 128)
                    if any(abs(dist - r) < 3 for r in range(110, 10, -18)):
                        set_pixel(x, y, (80, 245, 255))
                    if dist < 22:
                        set_pixel(x, y, (12, 126, 142))
        else:
            for i in range(-256, 256, 36):
                line_diag(i, (255, 180, 64), 6)
                line_diag(i + 18, (96, 52, 20), 3)
        write_tga(OUT / info["texture"], pixels)


def write_tga(path: Path, pixels: list[list[tuple[int, int, int]]]) -> None:
    height = len(pixels)
    width = len(pixels[0])
    header = bytearray(18)
    header[2] = 2
    header[12:14] = width.to_bytes(2, "little")
    header[14:16] = height.to_bytes(2, "little")
    header[16] = 24
    header[17] = 0x20
    body = bytearray()
    for row in pixels:
        for r, g, b in row:
            body.extend((b, g, r))
    path.write_bytes(bytes(header) + bytes(body))


def write_png(path: Path, width: int, height: int, pixels: list[list[tuple[int, int, int]]]) -> None:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    raw = bytearray()
    for row in pixels:
        raw.append(0)
        for r, g, b in row:
            raw.extend((r, g, b))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))


def write_mtl(path: Path) -> None:
    lines = []
    for material, info in MATERIALS.items():
        kd = info["kd"]
        lines.extend([
            f"newmtl {material}",
            f"Kd {kd[0]:.3f} {kd[1]:.3f} {kd[2]:.3f}",
            f"map_Kd {info['texture']}",
            "",
        ])
    path.write_text("\n".join(lines), encoding="ascii")


def write_skin() -> None:
    lines = [
        f"{material},models/props/{PROP_NAME}/{Path(info['texture']).stem}"
        for material, info in MATERIALS.items()
    ]
    (OUT / f"{PROP_NAME}_0.skin").write_text("\n".join(lines) + "\n", encoding="ascii")


def write_preview() -> None:
    width, height = 1280, 720
    pixels = [[(17, 20, 24) for _ in range(width)] for _ in range(height)]

    def rect(x0: int, y0: int, x1: int, y1: int, color: tuple[int, int, int]) -> None:
        for y in range(max(0, y0), min(height, y1 + 1)):
            for x in range(max(0, x0), min(width, x1 + 1)):
                pixels[y][x] = color

    def outline(x0: int, y0: int, x1: int, y1: int, color: tuple[int, int, int], w: int = 4) -> None:
        rect(x0, y0, x1, y0 + w, color)
        rect(x0, y1 - w, x1, y1, color)
        rect(x0, y0, x0 + w, y1, color)
        rect(x1 - w, y0, x1, y1, color)

    def circle(cx: int, cy: int, r: int, color: tuple[int, int, int]) -> None:
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                dist = math.hypot(x - cx, y - cy)
                if r - 4 <= dist <= r:
                    if 0 <= x < width and 0 <= y < height:
                        pixels[y][x] = color

    rect(80, 500, 1180, 590, (42, 47, 51))
    outline(210, 180, 1070, 510, (96, 110, 116), 16)
    for x in (300, 500, 700, 900):
        rect(x, 220, x + 120, 430, (31, 86, 79))
        outline(x, 220, x + 120, 430, (100, 210, 190), 4)
        for cx in (x + 38, x + 82):
            circle(cx, 300, 24, (40, 205, 218))
            rect(cx, 298, cx + 24, 302, (40, 205, 218))
            rect(cx - 2, 276, cx + 2, 300, (40, 205, 218))
    labels = [
        ("rig frame", MATERIALS["rig_frame"]["color"]),
        ("gpu boards", MATERIALS["gpu_board"]["color"]),
        ("fan glow", MATERIALS["fan_glow"]["color"]),
        ("rtc cables", MATERIALS["rtc_cable"]["color"]),
    ]
    for i, (_, color) in enumerate(labels):
        x = 80 + i * 250
        rect(x, 625, x + 48, 673, color)
    write_png(OUT / f"{PROP_NAME}_preview.png", width, height, pixels)


def generate() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    base_ns["PROP_NAME"] = PROP_NAME
    base_ns["MATERIALS"] = MATERIALS
    mesh = build_mesh()
    mesh.write(OUT / f"{PROP_NAME}_source.obj", f"{PROP_NAME}_source.mtl")
    write_mtl(OUT / f"{PROP_NAME}_source.mtl")
    write_iqm_direct(OUT / f"{PROP_NAME}.iqm", mesh)
    write_textures()
    write_skin()
    write_preview()
    (OUT / "README.md").write_text(README_TEXT, encoding="utf-8")
    (OUT / "LICENSE").write_text(LICENSE_TEXT, encoding="utf-8")


if __name__ == "__main__":
    generate()
