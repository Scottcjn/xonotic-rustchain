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
SEED = 0x6D656D70


def font(size: int) -> ImageFont.ImageFont:
    for name in ("DejaVuSans-Bold.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def clamp(value: int) -> int:
    return max(0, min(255, value))


def add_packet_noise(base: Image.Image) -> None:
    pixels = base.load()
    for y in range(SIZE):
        for x in range(SIZE):
            wave = int(7 * math.sin(x / 27.0) + 6 * math.cos(y / 31.0))
            cell = ((x // 22) ^ (y // 22)) & 1
            delta = wave + (8 if cell else -5)
            r, g, b = pixels[x, y]
            pixels[x, y] = (clamp(r + delta), clamp(g + delta + 2), clamp(b + delta))


def polygon(draw: ImageDraw.ImageDraw, points, fill, outline, width=3) -> None:
    draw.polygon(points, fill=fill)
    draw.line(points + [points[0]], fill=outline, width=width, joint="curve")


def draw_packet(draw: ImageDraw.ImageDraw, glow: ImageDraw.ImageDraw, x: int, y: int, size: int, fill, outline, label: str) -> None:
    draw.rounded_rectangle((x, y, x + size, y + size), radius=max(6, size // 6), fill=fill, outline=outline, width=2)
    draw.line((x + 8, y + size // 2, x + size - 8, y + size // 2), fill=outline, width=2)
    draw.text((x + 8, y + size // 2 + 4), label, fill=(220, 252, 246), font=font(max(13, size // 4)))
    glow.rounded_rectangle((x - 2, y - 2, x + size + 2, y + size + 2), radius=max(8, size // 6), outline=outline, width=5)


def draw_swarm(draw: ImageDraw.ImageDraw, glow: ImageDraw.ImageDraw, rng: random.Random) -> None:
    teal = (60, 235, 204)
    amber = (255, 197, 72)
    core = (222, 255, 246)
    centers = []
    for _ in range(64):
        x = rng.randrange(90, 934)
        y = rng.randrange(110, 920)
        radius = rng.randrange(9, 20)
        color = teal if rng.random() < 0.72 else amber
        centers.append((x, y, color))
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(24, 47, 50), outline=color, width=2)
        draw.ellipse((x - 4, y - 4, x + 4, y + 4), fill=core)
        glow.ellipse((x - radius - 4, y - radius - 4, x + radius + 4, y + radius + 4), fill=color)

    for index, (x, y, color) in enumerate(centers):
        for j in range(index + 1, min(index + 5, len(centers))):
            x2, y2, _ = centers[j]
            if (x - x2) ** 2 + (y - y2) ** 2 < 36000:
                draw.line((x, y, x2, y2), fill=color, width=2)
                glow.line((x, y, x2, y2), fill=color, width=5)


def make_diffuse_and_glow() -> tuple[Image.Image, Image.Image]:
    rng = random.Random(SEED)
    diffuse = Image.new("RGB", (SIZE, SIZE), (16, 24, 27))
    glow = Image.new("RGB", (SIZE, SIZE), (0, 0, 0))
    add_packet_noise(diffuse)

    d = ImageDraw.Draw(diffuse)
    g = ImageDraw.Draw(glow)

    teal = (60, 235, 204)
    teal_dark = (24, 69, 70)
    amber = (255, 197, 72)
    dark = (27, 38, 43)
    mid = (39, 54, 60)
    violet = (137, 103, 255)

    plates = [
        [(358, 62), (666, 62), (700, 256), (512, 326), (324, 256)],
        [(278, 340), (746, 340), (698, 708), (512, 786), (326, 708)],
        [(68, 312), (266, 356), (224, 744), (44, 686)],
        [(758, 356), (956, 312), (980, 686), (800, 744)],
        [(310, 770), (498, 804), (452, 970), (276, 970)],
        [(526, 804), (714, 770), (748, 970), (572, 970)],
        [(24, 82), (190, 82), (190, 252), (24, 252)],
        [(834, 82), (1000, 82), (1000, 252), (834, 252)],
    ]
    fills = [mid, dark, dark, dark, (25, 42, 45), (25, 42, 45), (22, 35, 39), (22, 35, 39)]
    outlines = [teal, teal, amber, amber, teal, amber, violet, violet]
    for pts, fill, outline in zip(plates, fills, outlines):
        polygon(d, pts, fill, outline)

    draw_swarm(d, g, rng)

    # Queue bands and priority fee lanes.
    for lane, y in enumerate((410, 470, 530, 590, 650)):
        color = teal if lane % 2 == 0 else amber
        d.line((318, y, 704, y + int(18 * math.sin(lane))), fill=color, width=6)
        g.line((318, y, 704, y + int(18 * math.sin(lane))), fill=color, width=14)
        for x in range(344, 684, 68):
            draw_packet(d, g, x, y - 20, 42, teal_dark, color, f"{rng.randrange(10, 99)}")

    d.ellipse((444, 432, 580, 568), fill=(11, 45, 49), outline=(221, 255, 246), width=5)
    d.ellipse((478, 466, 546, 534), fill=teal)
    g.ellipse((426, 414, 598, 586), fill=teal)
    d.text((482, 488), "tx", fill=(12, 38, 40), font=font(31))

    title_font = font(60)
    small_font = font(30)
    d.text((348, 260), "MEMPOOL", fill=(225, 255, 247), font=title_font)
    d.text((70, 258), "pending", fill=(208, 255, 246), font=small_font)
    d.text((814, 258), "fee lane", fill=(255, 228, 154), font=small_font)
    d.text((378, 714), "queued tx swarm", fill=(197, 235, 231), font=small_font)

    hex_chars = "0123456789abcdef"
    for _ in range(120):
        x = rng.randrange(36, SIZE - 110)
        y = rng.randrange(34, SIZE - 34)
        text = "".join(rng.choice(hex_chars) for _ in range(4))
        color = (rng.randrange(78, 142), rng.randrange(174, 245), rng.randrange(170, 238))
        d.text((x, y), text, fill=color, font=font(17))

    for _ in range(260):
        x = rng.randrange(SIZE)
        y = rng.randrange(SIZE)
        radius = rng.randrange(2, 6)
        color = (rng.randrange(22, 66), rng.randrange(52, 102), rng.randrange(56, 108))
        d.rectangle((x, y, x + radius, y + radius), fill=color)

    glow = glow.filter(ImageFilter.GaussianBlur(2.1))
    return diffuse, glow


def make_preview(diffuse: Image.Image, glow: Image.Image) -> Image.Image:
    canvas = Image.new("RGB", (1400, 760), (14, 19, 22))
    bg = diffuse.resize((700, 700)).filter(ImageFilter.GaussianBlur(4))
    canvas.paste(bg, (0, 30))

    d = ImageDraw.Draw(canvas)
    d.rectangle((0, 0, 1400, 760), outline=(60, 235, 204), width=3)
    d.text((760, 86), "RustChain Mempool", fill=(225, 255, 247), font=font(58))
    d.text((762, 160), "Queued transaction swarm player skin", fill=(186, 207, 205), font=font(31))
    d.text((762, 224), "Diffuse + glow maps, 1024x1024 TGA", fill=(186, 207, 205), font=font(28))
    d.text((762, 268), "CC-BY-SA-4.0, deterministic procedural source", fill=(186, 207, 205), font=font(28))

    avatar = Image.new("RGBA", (420, 520), (0, 0, 0, 0))
    a = ImageDraw.Draw(avatar)
    teal = (60, 235, 204)
    amber = (255, 197, 72)
    a.ellipse((156, 20, 264, 128), fill=(36, 52, 56), outline=teal, width=5)
    a.rounded_rectangle((112, 128, 308, 322), radius=34, fill=(35, 48, 53), outline=teal, width=5)
    a.ellipse((184, 194, 236, 246), fill=teal, outline=(225, 255, 247), width=3)
    a.polygon([(112, 164), (34, 292), (78, 328), (140, 220)], fill=(30, 44, 48), outline=amber)
    a.polygon([(308, 164), (388, 292), (342, 328), (280, 220)], fill=(30, 44, 48), outline=amber)
    a.polygon([(146, 322), (210, 322), (190, 505), (112, 505)], fill=(27, 42, 45), outline=teal)
    a.polygon([(210, 322), (276, 322), (308, 505), (230, 505)], fill=(27, 42, 45), outline=teal)
    for i in range(22):
        x = 100 + (i * 37) % 220
        y = 74 + (i * 61) % 360
        color = teal if i % 3 else amber
        a.ellipse((x - 7, y - 7, x + 7, y + 7), fill=color)
        if i > 0:
            a.line((x, y, 210, 216), fill=color, width=2)
    avatar = avatar.resize((340, 421), Image.Resampling.LANCZOS)
    canvas.paste(avatar, (850, 318), avatar)

    diff_thumb = diffuse.resize((190, 190))
    glow_thumb = glow.resize((190, 190))
    canvas.paste(diff_thumb, (70, 500))
    canvas.paste(glow_thumb, (284, 500))
    d.rectangle((70, 500, 260, 690), outline=(225, 255, 247), width=2)
    d.rectangle((284, 500, 474, 690), outline=(225, 255, 247), width=2)
    d.text((70, 704), "diffuse", fill=(225, 255, 247), font=font(23))
    d.text((284, 704), "glow", fill=(225, 255, 247), font=font(23))
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
