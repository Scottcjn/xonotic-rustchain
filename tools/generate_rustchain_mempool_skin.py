#!/usr/bin/env python3
"""Generate the RustChain Mempool player-skin texture pack.

The output is deterministic and self-contained so reviewers can regenerate the
submitted TGA/PNG assets from source.
"""

from pathlib import Path
import math
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "pk3_build" / "models" / "player" / "skins" / "rustchain_mempool"
SIZE = 1024
SEED = 0x6D454D50


def font(size: int) -> ImageFont.ImageFont:
    for name in ("DejaVuSans-Bold.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def clamp(value: int) -> int:
    return max(0, min(255, value))


def add_backlog_noise(base: Image.Image) -> None:
    pixels = base.load()
    for y in range(SIZE):
        for x in range(SIZE):
            row_wave = int(9 * math.sin(y / 21.0))
            column_wave = int(7 * math.sin((x + y) / 47.0))
            cell = 8 if ((x // 28) + (y // 18)) % 3 == 0 else -5
            r, g, b = pixels[x, y]
            pixels[x, y] = (
                clamp(r + cell + row_wave // 2),
                clamp(g + cell + column_wave),
                clamp(b + row_wave + column_wave),
            )


def polygon(draw: ImageDraw.ImageDraw, points, fill, outline, width=3) -> None:
    draw.polygon(points, fill=fill)
    draw.line(points + [points[0]], fill=outline, width=width, joint="curve")


def draw_packet_node(
    draw: ImageDraw.ImageDraw,
    glow: ImageDraw.ImageDraw,
    x: int,
    y: int,
    size: int,
    fill,
    outline,
    label: str,
) -> None:
    box = (x - size, y - size, x + size, y + size)
    draw.rounded_rectangle(box, radius=max(5, size // 3), fill=fill, outline=outline, width=3)
    draw.text((x - size + 5, y - 10), label, fill=(232, 255, 248), font=font(max(14, size // 2)))
    glow.rounded_rectangle((box[0] - 5, box[1] - 5, box[2] + 5, box[3] + 5), radius=max(8, size // 2), fill=outline)


def draw_swarm(draw: ImageDraw.ImageDraw, glow: ImageDraw.ImageDraw, rng: random.Random) -> None:
    cyan = (70, 235, 255)
    green = (91, 255, 175)
    violet = (217, 87, 255)
    amber = (255, 195, 79)
    nodes = []
    for band, y in enumerate((142, 226, 324, 438, 544, 662, 804, 910)):
        for i in range(7):
            x = 96 + i * 130 + rng.randint(-18, 18)
            ny = y + rng.randint(-28, 28)
            nodes.append((x, ny, band, i))

    for index, (x, y, band, i) in enumerate(nodes):
        color = (cyan, green, violet, amber)[(band + i) % 4]
        if index + 1 < len(nodes):
            nx, ny, _, _ = nodes[index + 1]
            if abs(nx - x) < 190:
                draw.line((x, y, nx, ny), fill=(38, 94, 108), width=3)
                glow.line((x, y, nx, ny), fill=color, width=10)
        label = f"{rng.randrange(0, 9999):04x}"[-3:]
        draw_packet_node(draw, glow, x, y, 24 + (i % 3) * 4, (25, 34, 44), color, label)


def draw_body_panels(draw: ImageDraw.ImageDraw, glow: ImageDraw.ImageDraw) -> None:
    cyan = (70, 235, 255)
    green = (91, 255, 175)
    violet = (217, 87, 255)
    amber = (255, 195, 79)
    dark = (26, 33, 43)
    steel = (42, 54, 66)

    plates = [
        [(348, 58), (676, 58), (706, 258), (512, 332), (318, 258)],
        [(274, 350), (750, 350), (706, 724), (512, 790), (318, 724)],
        [(58, 304), (262, 350), (220, 748), (32, 680)],
        [(762, 350), (966, 304), (992, 680), (804, 748)],
        [(306, 792), (494, 826), (454, 976), (280, 976)],
        [(530, 826), (718, 792), (744, 976), (570, 976)],
    ]
    outlines = (green, cyan, violet, amber, green, cyan)
    for index, pts in enumerate(plates):
        polygon(draw, pts, steel if index < 2 else dark, outlines[index], width=4)
        glow.line(pts + [pts[0]], fill=outlines[index], width=10, joint="curve")

    draw.rounded_rectangle((380, 412, 644, 584), radius=28, fill=(15, 25, 32), outline=green, width=5)
    glow.rounded_rectangle((364, 396, 660, 600), radius=36, fill=(42, 196, 128))
    for i, y in enumerate(range(432, 562, 26)):
        color = (green, cyan, violet, amber)[i % 4]
        draw.rounded_rectangle((412, y, 612 - i * 8, y + 13), radius=6, fill=color)
        glow.rounded_rectangle((404, y - 4, 620 - i * 8, y + 17), radius=8, fill=color)

    draw.text((344, 272), "MEMPOOL", fill=(232, 255, 248), font=font(62))
    draw.text((392, 596), "TX QUEUE", fill=amber, font=font(30))
    draw.text((72, 258), "pending", fill=green, font=font(28))
    draw.text((804, 258), "fee lane", fill=violet, font=font(28))


def make_diffuse_and_glow() -> tuple[Image.Image, Image.Image]:
    rng = random.Random(SEED)
    diffuse = Image.new("RGB", (SIZE, SIZE), (16, 21, 29))
    glow = Image.new("RGB", (SIZE, SIZE), (0, 0, 0))
    add_backlog_noise(diffuse)

    d = ImageDraw.Draw(diffuse)
    g = ImageDraw.Draw(glow)
    draw_body_panels(d, g)
    draw_swarm(d, g, rng)

    for _ in range(120):
        x = rng.randrange(24, SIZE - 78)
        y = rng.randrange(36, SIZE - 36)
        fee = rng.choice(("1sat", "2sat", "5sat", "push", "rpl", "wait"))
        color = rng.choice(((117, 255, 186), (86, 231, 255), (226, 108, 255), (255, 207, 96)))
        d.text((x, y), fee, fill=color, font=font(17))

    for _ in range(260):
        x = rng.randrange(SIZE)
        y = rng.randrange(SIZE)
        side = rng.randrange(2, 7)
        color = (
            rng.randrange(28, 58),
            rng.randrange(44, 90),
            rng.randrange(54, 116),
        )
        d.rectangle((x, y, x + side, y + side), fill=color)

    glow = glow.filter(ImageFilter.GaussianBlur(2.3))
    return diffuse, glow


def make_preview(diffuse: Image.Image, glow: Image.Image) -> Image.Image:
    canvas = Image.new("RGB", (1400, 760), (13, 17, 24))
    bg = diffuse.resize((700, 700)).filter(ImageFilter.GaussianBlur(4))
    canvas.paste(bg, (0, 30))

    d = ImageDraw.Draw(canvas)
    green = (91, 255, 175)
    cyan = (70, 235, 255)
    violet = (217, 87, 255)
    amber = (255, 195, 79)
    d.rectangle((0, 0, 1400, 760), outline=green, width=3)
    d.text((760, 86), "RustChain Mempool", fill=(232, 255, 248), font=font(56))
    d.text((762, 158), "Cluster swarm player skin", fill=(190, 208, 214), font=font(31))
    d.text((762, 222), "Diffuse + glow maps, 1024x1024 TGA", fill=(190, 208, 214), font=font(28))
    d.text((762, 266), "CC-BY-SA-4.0, deterministic procedural source", fill=(190, 208, 214), font=font(28))

    avatar = Image.new("RGBA", (420, 520), (0, 0, 0, 0))
    a = ImageDraw.Draw(avatar)
    a.ellipse((156, 20, 264, 128), fill=(38, 50, 60), outline=green, width=5)
    a.rounded_rectangle((106, 128, 314, 326), radius=34, fill=(34, 43, 54), outline=cyan, width=5)
    a.rounded_rectangle((150, 178, 270, 268), radius=18, fill=(18, 28, 36), outline=green, width=4)
    for i, y in enumerate(range(194, 252, 16)):
        color = (green, cyan, violet, amber)[i % 4]
        a.rounded_rectangle((166, y, 254 - i * 10, y + 8), radius=4, fill=color)
    a.polygon([(106, 164), (30, 292), (78, 334), (144, 224)], fill=(30, 39, 50), outline=violet)
    a.polygon([(314, 164), (390, 292), (342, 334), (276, 224)], fill=(30, 39, 50), outline=amber)
    a.polygon([(146, 326), (210, 326), (190, 505), (112, 505)], fill=(26, 35, 45), outline=green)
    a.polygon([(210, 326), (276, 326), (308, 505), (230, 505)], fill=(26, 35, 45), outline=cyan)
    for x, y, color in ((112, 84, green), (262, 150, cyan), (88, 384, violet), (300, 408, amber)):
        a.rounded_rectangle((x, y, x + 44, y + 30), radius=8, fill=(18, 26, 34), outline=color, width=3)
        a.line((x + 44, y + 15, 210, 224), fill=color, width=4)
    avatar = avatar.resize((340, 421), Image.Resampling.LANCZOS)
    canvas.paste(avatar, (850, 318), avatar)

    diff_thumb = diffuse.resize((190, 190))
    glow_thumb = glow.resize((190, 190))
    canvas.paste(diff_thumb, (70, 500))
    canvas.paste(glow_thumb, (284, 500))
    d.rectangle((70, 500, 260, 690), outline=(232, 255, 248), width=2)
    d.rectangle((284, 500, 474, 690), outline=(232, 255, 248), width=2)
    d.text((70, 704), "diffuse", fill=(232, 255, 248), font=font(23))
    d.text((284, 704), "glow", fill=(232, 255, 248), font=font(23))
    return canvas


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    diffuse, glow = make_diffuse_and_glow()
    preview = make_preview(diffuse, glow)

    diffuse.save(OUT / "rustchain_mempool_diffuse.tga")
    glow.save(OUT / "rustchain_mempool_glow.tga")
    preview.save(OUT / "rustchain_mempool_preview.png")


if __name__ == "__main__":
    main()
