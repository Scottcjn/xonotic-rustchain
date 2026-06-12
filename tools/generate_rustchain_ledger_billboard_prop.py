#!/usr/bin/env python3
"""Generate the RustChain ledger billboard prop package.

The model is intentionally low-poly and deterministic so reviewers can
regenerate every submitted file from source.
"""

from __future__ import annotations

from pathlib import Path
import math
import random
import struct

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "pk3_build" / "models" / "props" / "rustchain_ledger_billboard"
TEXTURES = OUT / "textures"
SEED = 0x1ED6E7
TEX_SIZE = 256

MATERIALS = {
    "frame": "textures/ledger_billboard_frame.tga",
    "screen": "textures/ledger_billboard_panel.tga",
    "glow": "textures/ledger_billboard_glow.tga",
}


def font(size: int) -> ImageFont.ImageFont:
    for name in ("DejaVuSans-Bold.ttf", "Arial Bold.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def make_frame_texture() -> Image.Image:
    image = Image.new("RGB", (TEX_SIZE, TEX_SIZE), (42, 45, 43))
    pixels = image.load()
    for y in range(TEX_SIZE):
        for x in range(TEX_SIZE):
            grain = int(9 * math.sin((x + 11) / 13.0) + 6 * math.cos((y + 5) / 17.0))
            seam = 20 if x % 64 in (0, 1, 62, 63) or y % 64 in (0, 1, 62, 63) else 0
            base = 48 + grain - seam
            pixels[x, y] = (max(18, base), max(20, base + 6), max(19, base + 3))

    draw = ImageDraw.Draw(image)
    for x in range(18, TEX_SIZE, 47):
        draw.line((x, 0, x - 36, TEX_SIZE), fill=(94, 100, 93), width=2)
    for x, y in ((22, 22), (232, 22), (22, 232), (232, 232), (128, 28), (128, 228)):
        draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=(16, 18, 17), outline=(118, 130, 119))
    draw.rectangle((8, 8, 247, 247), outline=(114, 126, 117), width=3)
    return image


def make_panel_texture() -> Image.Image:
    rng = random.Random(SEED)
    image = Image.new("RGB", (TEX_SIZE, TEX_SIZE), (8, 21, 24))
    draw = ImageDraw.Draw(image)

    for y in range(TEX_SIZE):
        shade = int(16 + 8 * math.sin(y / 18.0))
        draw.line((0, y, TEX_SIZE, y), fill=(7, 24 + shade // 4, 25 + shade))

    draw.rectangle((8, 8, 247, 247), outline=(66, 240, 201), width=3)
    draw.rectangle((16, 18, 240, 72), outline=(255, 190, 72), width=2)
    draw.text((24, 24), "LEDGER LIVE", fill=(224, 255, 246), font=font(24))
    draw.text((25, 51), "block 000742", fill=(255, 219, 126), font=font(15))

    hexchars = "0123456789abcdef"
    for row in range(8):
        y = 88 + row * 18
        prefix = "tx " if row % 2 else "rt "
        value = "".join(rng.choice(hexchars) for _ in range(16))
        color = (80, 236, 205) if row % 3 else (255, 198, 73)
        draw.text((20, y), prefix + value, fill=color, font=font(13))
        draw.line((18, y + 15, 238, y + 15), fill=(16, 65, 61), width=1)

    for index in range(14):
        x = 22 + (index % 7) * 31
        y = 212 + (index // 7) * 18
        draw.rectangle((x, y, x + 18, y + 10), fill=(18, 69, 66), outline=(78, 244, 205))
        if index > 0:
            px = 22 + ((index - 1) % 7) * 31 + 18
            py = 212 + ((index - 1) // 7) * 18 + 5
            draw.line((px, py, x, y + 5), fill=(78, 244, 205), width=1)

    return image


def make_glow_texture() -> Image.Image:
    image = Image.new("RGB", (TEX_SIZE, TEX_SIZE), (0, 0, 0))
    draw = ImageDraw.Draw(image)
    for radius, color in (
        (118, (10, 54, 45)),
        (86, (20, 110, 92)),
        (58, (42, 205, 174)),
        (30, (210, 255, 239)),
    ):
        draw.ellipse((128 - radius, 128 - radius, 128 + radius, 128 + radius), fill=color)
    draw.text((75, 111), "RTC", fill=(4, 36, 31), font=font(42))
    return image


def vec_sub(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def cross(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def normalize(v: tuple[float, float, float]) -> tuple[float, float, float]:
    length = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
    if length == 0:
        return (0.0, 0.0, 1.0)
    return (v[0] / length, v[1] / length, v[2] / length)


class MeshBuilder:
    def __init__(self) -> None:
        self.groups: dict[str, list[tuple[list[tuple[float, float, float]], list[tuple[float, float]]]]] = {
            key: [] for key in MATERIALS
        }

    def add_quad(
        self,
        material: str,
        points: list[tuple[float, float, float]],
        uvs: list[tuple[float, float]] | None = None,
    ) -> None:
        if uvs is None:
            uvs = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
        self.groups[material].append((points, uvs))

    def add_box(
        self,
        material: str,
        center: tuple[float, float, float],
        size: tuple[float, float, float],
    ) -> None:
        cx, cy, cz = center
        sx, sy, sz = (size[0] / 2.0, size[1] / 2.0, size[2] / 2.0)
        x0, x1 = cx - sx, cx + sx
        y0, y1 = cy - sy, cy + sy
        z0, z1 = cz - sz, cz + sz
        self.add_quad(material, [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)])
        self.add_quad(material, [(x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)])
        self.add_quad(material, [(x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)])
        self.add_quad(material, [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)])
        self.add_quad(material, [(x0, y1, z1), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1)])
        self.add_quad(material, [(x0, y0, z0), (x0, y1, z0), (x1, y1, z0), (x1, y0, z0)])

    def build(self):
        vertices: list[tuple[float, float, float]] = []
        texcoords: list[tuple[float, float]] = []
        normals: list[tuple[float, float, float]] = []
        tangents: list[tuple[float, float, float, float]] = []
        triangles: list[tuple[int, int, int]] = []
        mesh_ranges = []

        for material, quads in self.groups.items():
            first_vertex = len(vertices)
            first_triangle = len(triangles)
            for points, uvs in quads:
                normal = normalize(cross(vec_sub(points[1], points[0]), vec_sub(points[2], points[0])))
                tangent3 = normalize(vec_sub(points[1], points[0]))
                base = len(vertices)
                for point, uv in zip(points, uvs):
                    vertices.append(point)
                    texcoords.append(uv)
                    normals.append(normal)
                    tangents.append((tangent3[0], tangent3[1], tangent3[2], 1.0))
                triangles.append((base, base + 1, base + 2))
                triangles.append((base, base + 2, base + 3))
            mesh_ranges.append((material, first_vertex, len(vertices) - first_vertex, first_triangle, len(triangles) - first_triangle))
        return vertices, texcoords, normals, tangents, triangles, mesh_ranges


def make_mesh() -> MeshBuilder:
    mesh = MeshBuilder()
    mesh.add_box("frame", (0.0, 0.0, 1.55), (2.25, 0.18, 1.05))
    mesh.add_box("screen", (0.0, -0.115, 1.58), (1.82, 0.035, 0.72))
    mesh.add_box("frame", (-0.98, 0.0, 0.62), (0.14, 0.14, 1.24))
    mesh.add_box("frame", (0.98, 0.0, 0.62), (0.14, 0.14, 1.24))
    mesh.add_box("frame", (-0.98, 0.0, 0.03), (0.46, 0.34, 0.06))
    mesh.add_box("frame", (0.98, 0.0, 0.03), (0.46, 0.34, 0.06))
    mesh.add_box("frame", (0.0, 0.0, 2.16), (2.42, 0.22, 0.14))
    mesh.add_box("frame", (0.0, 0.0, 0.96), (2.42, 0.22, 0.12))
    mesh.add_box("glow", (-0.72, -0.14, 1.14), (0.18, 0.045, 0.18))
    mesh.add_box("glow", (0.0, -0.14, 1.14), (0.18, 0.045, 0.18))
    mesh.add_box("glow", (0.72, -0.14, 1.14), (0.18, 0.045, 0.18))
    mesh.add_box("glow", (-1.05, -0.13, 2.17), (0.12, 0.045, 0.12))
    mesh.add_box("glow", (1.05, -0.13, 2.17), (0.12, 0.045, 0.12))
    mesh.add_box("frame", (-0.34, 0.0, 2.42), (0.08, 0.08, 0.42))
    mesh.add_box("frame", (0.34, 0.0, 2.42), (0.08, 0.08, 0.42))
    mesh.add_box("glow", (-0.34, -0.02, 2.66), (0.17, 0.04, 0.08))
    mesh.add_box("glow", (0.34, -0.02, 2.66), (0.17, 0.04, 0.08))
    return mesh


def write_obj(mesh: MeshBuilder) -> None:
    vertices, texcoords, _, _, triangles, mesh_ranges = mesh.build()
    lines = ["mtllib rustchain_ledger_billboard.mtl", "o rustchain_ledger_billboard"]
    for vertex in vertices:
        lines.append(f"v {vertex[0]:.4f} {vertex[1]:.4f} {vertex[2]:.4f}")
    for uv in texcoords:
        lines.append(f"vt {uv[0]:.4f} {uv[1]:.4f}")

    for material, _, _, first_triangle, triangle_count in mesh_ranges:
        lines.append(f"usemtl {material}")
        for tri in triangles[first_triangle : first_triangle + triangle_count]:
            a, b, c = (index + 1 for index in tri)
            lines.append(f"f {a}/{a} {b}/{b} {c}/{c}")
    (OUT / "rustchain_ledger_billboard.obj").write_text("\n".join(lines) + "\n")


def write_mtl_and_skin() -> None:
    mtl = [
        "newmtl frame",
        "Kd 0.18 0.20 0.18",
        "map_Kd textures/ledger_billboard_frame.tga",
        "",
        "newmtl screen",
        "Kd 0.03 0.18 0.16",
        "map_Kd textures/ledger_billboard_panel.tga",
        "",
        "newmtl glow",
        "Kd 0.25 1.0 0.78",
        "map_Kd textures/ledger_billboard_glow.tga",
        "",
    ]
    (OUT / "rustchain_ledger_billboard.mtl").write_text("\n".join(mtl))
    skin = [
        "frame,models/props/rustchain_ledger_billboard/textures/ledger_billboard_frame.tga",
        "screen,models/props/rustchain_ledger_billboard/textures/ledger_billboard_panel.tga",
        "glow,models/props/rustchain_ledger_billboard/textures/ledger_billboard_glow.tga",
    ]
    (OUT / "rustchain_ledger_billboard.skin").write_text("\n".join(skin) + "\n")


def write_iqm(mesh: MeshBuilder) -> None:
    vertices, texcoords, normals, tangents, triangles, mesh_ranges = mesh.build()
    strings = ["rustchain_ledger_billboard_" + material for material in MATERIALS] + list(MATERIALS)
    text = b""
    offsets: dict[str, int] = {}
    for item in strings:
        offsets[item] = len(text)
        text += item.encode("utf-8") + b"\0"

    header_size = 124
    ofs_text = header_size
    ofs_meshes = ofs_text + len(text)
    mesh_records = b"".join(
        struct.pack(
            "<6I",
            offsets["rustchain_ledger_billboard_" + material],
            offsets[material],
            first_vertex,
            vertex_count,
            first_triangle,
            triangle_count,
        )
        for material, first_vertex, vertex_count, first_triangle, triangle_count in mesh_ranges
    )
    ofs_vertexarrays = ofs_meshes + len(mesh_records)
    vertex_array_records_size = 4 * 20
    ofs_position = ofs_vertexarrays + vertex_array_records_size
    position_data = b"".join(struct.pack("<3f", *value) for value in vertices)
    ofs_texcoord = ofs_position + len(position_data)
    texcoord_data = b"".join(struct.pack("<2f", *value) for value in texcoords)
    ofs_normal = ofs_texcoord + len(texcoord_data)
    normal_data = b"".join(struct.pack("<3f", *value) for value in normals)
    ofs_tangent = ofs_normal + len(normal_data)
    tangent_data = b"".join(struct.pack("<4f", *value) for value in tangents)
    ofs_triangles = ofs_tangent + len(tangent_data)
    triangle_data = b"".join(struct.pack("<3I", *value) for value in triangles)
    ofs_adjacency = ofs_triangles + len(triangle_data)
    adjacency_data = b"".join(struct.pack("<3I", 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF) for _ in triangles)
    filesize = ofs_adjacency + len(adjacency_data)

    vertex_arrays = b"".join(
        (
            struct.pack("<5I", 0, 0, 7, 3, ofs_position),
            struct.pack("<5I", 1, 0, 7, 2, ofs_texcoord),
            struct.pack("<5I", 2, 0, 7, 3, ofs_normal),
            struct.pack("<5I", 3, 0, 7, 4, ofs_tangent),
        )
    )

    header_values = [
        2,
        filesize,
        0,
        len(text),
        ofs_text,
        len(mesh_ranges),
        ofs_meshes,
        4,
        len(vertices),
        ofs_vertexarrays,
        len(triangles),
        ofs_triangles,
        ofs_adjacency,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
    ]
    header = b"INTERQUAKEMODEL\0" + struct.pack("<27I", *header_values)
    payload = b"".join(
        (
            header,
            text,
            mesh_records,
            vertex_arrays,
            position_data,
            texcoord_data,
            normal_data,
            tangent_data,
            triangle_data,
            adjacency_data,
        )
    )
    assert len(payload) == filesize
    (OUT / "rustchain_ledger_billboard.iqm").write_bytes(payload)


def make_preview(panel: Image.Image, frame: Image.Image, glow: Image.Image) -> Image.Image:
    canvas = Image.new("RGB", (960, 640), (13, 17, 18))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, 959, 639), outline=(63, 234, 200), width=3)
    draw.text((48, 42), "RustChain Ledger Billboard", fill=(229, 255, 247), font=font(42))
    draw.text((50, 96), "Xonotic Arena static prop / bounty #14015", fill=(183, 204, 199), font=font(23))

    frame_thumb = frame.resize((390, 232))
    canvas.paste(frame_thumb, (70, 180))
    draw.rounded_rectangle((100, 190, 430, 390), radius=12, fill=(42, 45, 43), outline=(124, 138, 126), width=8)
    canvas.paste(panel.resize((282, 130)), (124, 224))
    for x in (152, 250, 348):
        canvas.paste(glow.resize((48, 48)), (x, 366))
    draw.rectangle((116, 416, 146, 560), fill=(52, 58, 54), outline=(124, 138, 126), width=3)
    draw.rectangle((384, 416, 414, 560), fill=(52, 58, 54), outline=(124, 138, 126), width=3)
    draw.rectangle((82, 560, 180, 585), fill=(52, 58, 54), outline=(124, 138, 126), width=3)
    draw.rectangle((350, 560, 448, 585), fill=(52, 58, 54), outline=(124, 138, 126), width=3)

    draw.text((548, 190), "Includes", fill=(229, 255, 247), font=font(32))
    bullets = [
        "static IQM mesh",
        "editable OBJ + MTL source",
        "3 power-of-two TGA textures",
        "skin material mapping",
        "CC-BY-SA-4.0 license",
        "deterministic generator + tests",
    ]
    for index, text in enumerate(bullets):
        y = 242 + index * 44
        draw.rectangle((552, y + 7, 568, y + 23), fill=(63, 234, 200))
        draw.text((584, y), text, fill=(190, 216, 211), font=font(22))

    draw.text((548, 532), "Theme: live chain ledger display", fill=(255, 205, 91), font=font(24))
    return canvas


def write_readme_and_license() -> None:
    readme = """# RustChain Ledger Billboard Prop

Original low-poly static prop for the Xonotic RustChain Arena prop bounty #14015.

## Contents
- `rustchain_ledger_billboard.iqm` -- static IQM mesh for Xonotic packaging.
- `rustchain_ledger_billboard.obj` + `.mtl` -- editable source mesh.
- `textures/*.tga` -- 256x256 power-of-two diffuse/glow textures.
- `rustchain_ledger_billboard.skin` -- material mapping hint for frame, screen, and glow surfaces.
- `preview.png` -- generated preview render.
- `tools/generate_rustchain_ledger_billboard_prop.py` -- deterministic source generator.

## Integration
Suggested path: `pk3_build/models/props/rustchain_ledger_billboard/`.
Use near spawn corridors, score rooms, or capture-point approaches as a diegetic chain-status display. The prop footprint is about 2.4 x 0.35 x 2.7 units before mapper scaling.

## License
CC-BY-SA-4.0 / GPL-compatible for inclusion in the Xonotic RustChain Arena assets.
"""
    (OUT / "README.md").write_text(readme)
    license_text = """Creative Commons Attribution-ShareAlike 4.0 International

This RustChain Ledger Billboard prop package is original generated artwork.
It may be redistributed and adapted under CC-BY-SA-4.0 and is intended to be
GPL-compatible for inclusion in the Xonotic RustChain Arena asset set.
"""
    (OUT / "LICENSE").write_text(license_text)


def main() -> None:
    TEXTURES.mkdir(parents=True, exist_ok=True)
    frame = make_frame_texture()
    panel = make_panel_texture()
    glow = make_glow_texture()

    frame.save(TEXTURES / "ledger_billboard_frame.tga")
    panel.save(TEXTURES / "ledger_billboard_panel.tga")
    glow.save(TEXTURES / "ledger_billboard_glow.tga")
    make_preview(panel, frame, glow).save(OUT / "preview.png")

    mesh = make_mesh()
    write_obj(mesh)
    write_mtl_and_skin()
    write_iqm(mesh)
    write_readme_and_license()


if __name__ == "__main__":
    main()
