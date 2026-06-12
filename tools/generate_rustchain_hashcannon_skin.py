#!/usr/bin/env python3
"""Generate the RustChain HashCannon player-skin texture pack.

The output is deterministic and self-contained so reviewers can regenerate the
submitted TGA/PNG assets from source.
"""

from pathlib import Path
import math
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "pk3_build" / "models" / "player" / "skins" / "rustchain_hashcannon"
SIZE = 1024
SEED = 0xA511CA00


def font(size: int) -> ImageFont.ImageFont:
    for name in ("DejaVuSans-Bold.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def clamp(value: int) -> int:
    return max(0, min(255, value))


def add_graphite_grid(base: Image.Image) -> None:
    pixels = base.load()
    for y in range(SIZE):
        for x in range(SIZE):
            lattice = ((x // 20) + (y // 20)) & 1
            sweep = int(8 * math.sin((x + y) / 34.0))
            delta = 9 if lattice else -6
            r, g, b = pixels[x, y]
            pixels[x, y] = (clamp(r + delta + sweep), clamp(g + delta), clamp(b + delta - sweep))


def polygon(draw: ImageDraw.ImageDraw, points, fill, outline, width=3) -> None:
    draw.polygon(points, fill=fill)
    draw.line(points + [points[0]], fill=outline, width=width, joint="curve")


def hash_stream(draw: ImageDraw.ImageDraw, glow: ImageDraw.ImageDraw, start, count, color, core) -> None:
    x, y = start
    pts = []
    for i in range(count):
        pts.append((x + i * 42, y + int(22 * math.sin(i * 0.92 + x * 0.01))))
    draw.line(pts, fill=color, width=5, joint="curve")
    draw.line(pts, fill=core, width=1, joint="curve")
    glow.line(pts, fill=color, width=13, joint="curve")
    for px, py in pts:
        draw.rectangle((px - 11, py - 7, px + 11, py + 7), fill=(20, 25, 31), outline=core, width=2)
        draw.text((px - 7, py - 13), "#", fill=core, font=font(22))
        glow.rectangle((px - 13, py - 9, px + 13, py + 9), fill=color)


def railgun_barrel(draw: ImageDraw.ImageDraw, glow: ImageDraw.ImageDraw, center_y: int) -> None:
    rails = [
        [(166, center_y - 48), (780, center_y - 78), (890, center_y - 28), (216, center_y + 12)],
        [(170, center_y + 34), (790, center_y + 4), (894, center_y + 50), (220, center_y + 88)],
    ]
    for rail in rails:
        polygon(draw, rail, (39, 47, 57), (68, 229, 255), width=4)
        glow.line(rail + [rail[0]], fill=(54, 212, 255), width=9, joint="curve")

    draw.rounded_rectangle((192, center_y - 20, 846, center_y + 42), radius=24, fill=(18, 22, 29), outline=(206, 238, 250), width=4)
    draw.rounded_rectangle((292, center_y - 6, 792, center_y + 28), radius=16, fill=(28, 38, 48), outline=(111, 245, 255), width=2)
    glow.rounded_rectangle((286, center_y - 12, 798, center_y + 34), radius=20, fill=(24, 155, 197))

    for x in range(260, 790, 72):
        draw.line((x, center_y - 62, x + 32, center_y + 74), fill=(246, 207, 91), width=4)
        glow.line((x, center_y - 62, x + 32, center_y + 74), fill=(255, 203, 70), width=9)

    muzzle = [(828, center_y - 74), (974, center_y - 42), (972, center_y + 72), (828, center_y + 96)]
    polygon(draw, muzzle, (45, 52, 61), (255, 203, 70), width=4)
    draw.ellipse((902, center_y - 8, 956, center_y + 46), fill=(9, 15, 21), outline=(111, 245, 255), width=4)
    glow.ellipse((886, center_y - 24, 972, center_y + 62), fill=(46, 214, 255))


def make_diffuse_and_glow() -> tuple[Image.Image, Image.Image]:
    rng = random.Random(SEED)
    diffuse = Image.new("RGB", (SIZE, SIZE), (18, 22, 28))
    glow = Image.new("RGB", (SIZE, SIZE), (0, 0, 0))
    add_graphite_grid(diffuse)

    d = ImageDraw.Draw(diffuse)
    g = ImageDraw.Draw(glow)

    cyan = (58, 220, 255)
    cyan_core = (211, 251, 255)
    gold = (255, 201, 69)
    steel = (46, 54, 65)
    dark = (28, 34, 42)

    plates = [
        [(360, 62), (664, 62), (694, 260), (512, 320), (330, 260)],
        [(288, 338), (736, 338), (690, 706), (512, 774), (334, 706)],
        [(72, 320), (266, 356), (224, 734), (48, 682)],
        [(758, 356), (952, 320), (976, 682), (800, 734)],
        [(318, 768), (500, 802), (454, 970), (282, 970)],
        [(524, 802), (706, 768), (742, 970), (570, 970)],
        [(24, 86), (188, 86), (188, 250), (24, 250)],
        [(836, 86), (1000, 86), (1000, 250), (836, 250)],
    ]
    for index, pts in enumerate(plates):
        fill = steel if index in (0, 1) else dark
        outline = cyan if index % 2 == 0 else gold
        polygon(d, pts, fill, outline)

    # Bright reactor core and shoulder hash coils.
    d.ellipse((448, 424, 576, 552), fill=(12, 36, 44), outline=cyan_core, width=5)
    d.ellipse((480, 456, 544, 520), fill=cyan)
    g.ellipse((430, 406, 594, 570), fill=(44, 216, 255))

    railgun_barrel(d, g, 606)

    for y in (142, 236, 392, 488, 824, 910):
        hash_stream(d, g, (78 + rng.randint(0, 22), y), 10, cyan, cyan_core)
    for y in (174, 438, 740):
        hash_stream(d, g, (118 + rng.randint(0, 30), y), 8, gold, (255, 236, 181))

    title_font = font(56)
    small_font = font(29)
    d.text((310, 262), "HASHCANNON", fill=(226, 249, 255), font=title_font)
    d.text((394, 552), "RTC-RAIL", fill=gold, font=small_font)
    d.text((72, 260), "nonce", fill=(193, 243, 252), font=small_font)
    d.text((812, 260), "sha256", fill=(255, 228, 151), font=small_font)

    # Non-repeating hash fragments and compute flecks.
    hex_chars = "0123456789abcdef"
    for _ in range(80):
        x = rng.randrange(32, SIZE - 130)
        y = rng.randrange(36, SIZE - 36)
        text = "".join(rng.choice(hex_chars) for _ in range(6))
        color = (rng.randrange(95, 155), rng.randrange(168, 230), rng.randrange(188, 255))
        d.text((x, y), text, fill=color, font=font(18))

    for _ in range(240):
        x = rng.randrange(SIZE)
        y = rng.randrange(SIZE)
        side = rng.randrange(3, 8)
        color = (
            rng.randrange(36, 76),
            rng.randrange(52, 104),
            rng.randrange(64, 124),
        )
        d.rectangle((x, y, x + side, y + side), fill=color)

    # Crosshair hash aperture.
    for radius in (56, 82, 112):
        d.ellipse((512 - radius, 78 - radius // 3, 512 + radius, 78 + radius // 3), outline=cyan, width=3)
        g.ellipse((512 - radius, 78 - radius // 3, 512 + radius, 78 + radius // 3), outline=cyan, width=7)
    d.line((428, 78, 596, 78), fill=cyan_core, width=3)
    d.line((512, 34, 512, 122), fill=cyan_core, width=3)
    g.line((428, 78, 596, 78), fill=cyan, width=9)
    g.line((512, 34, 512, 122), fill=cyan, width=9)

    glow = glow.filter(ImageFilter.GaussianBlur(2.1))
    return diffuse, glow


def make_preview(diffuse: Image.Image, glow: Image.Image) -> Image.Image:
    canvas = Image.new("RGB", (1400, 760), (15, 18, 23))
    bg = diffuse.resize((700, 700)).filter(ImageFilter.GaussianBlur(4))
    canvas.paste(bg, (0, 30))

    d = ImageDraw.Draw(canvas)
    d.rectangle((0, 0, 1400, 760), outline=(58, 220, 255), width=3)
    d.text((760, 86), "RustChain HashCannon", fill=(226, 249, 255), font=font(56))
    d.text((762, 158), "Railgun compute player skin", fill=(188, 204, 212), font=font(31))
    d.text((762, 222), "Diffuse + glow maps, 1024x1024 TGA", fill=(188, 204, 212), font=font(28))
    d.text((762, 266), "CC-BY-SA-4.0, deterministic procedural source", fill=(188, 204, 212), font=font(28))

    avatar = Image.new("RGBA", (420, 520), (0, 0, 0, 0))
    a = ImageDraw.Draw(avatar)
    cyan = (58, 220, 255)
    gold = (255, 201, 69)
    steel = (44, 54, 64)
    a.ellipse((156, 20, 264, 128), fill=steel, outline=cyan, width=5)
    a.rounded_rectangle((112, 128, 308, 320), radius=34, fill=(38, 45, 55), outline=cyan, width=5)
    a.ellipse((184, 190, 236, 242), fill=cyan, outline=(229, 251, 255), width=3)
    a.line((60, 226, 360, 168), fill=gold, width=14)
    a.line((76, 254, 376, 196), fill=cyan, width=7)
    a.polygon([(112, 164), (34, 292), (78, 326), (140, 220)], fill=(34, 44, 54), outline=gold)
    a.polygon([(308, 164), (388, 292), (342, 326), (280, 220)], fill=(34, 44, 54), outline=gold)
    a.polygon([(146, 320), (210, 320), (190, 505), (112, 505)], fill=(30, 38, 47), outline=cyan)
    a.polygon([(210, 320), (276, 320), (308, 505), (230, 505)], fill=(30, 38, 47), outline=cyan)
    for y in (82, 176, 238, 390):
        a.text((132, y), "##", fill=(214, 250, 255), font=font(25))
        a.line((182, y + 10, 292, y - 14), fill=cyan, width=5)
    avatar = avatar.resize((340, 421), Image.Resampling.LANCZOS)
    canvas.paste(avatar, (850, 318), avatar)

    diff_thumb = diffuse.resize((190, 190))
    glow_thumb = glow.resize((190, 190))
    canvas.paste(diff_thumb, (70, 500))
    canvas.paste(glow_thumb, (284, 500))
    d.rectangle((70, 500, 260, 690), outline=(226, 249, 255), width=2)
    d.rectangle((284, 500, 474, 690), outline=(226, 249, 255), width=2)
    d.text((70, 704), "diffuse", fill=(226, 249, 255), font=font(23))
    d.text((284, 704), "glow", fill=(226, 249, 255), font=font(23))
    return canvas


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    diffuse, glow = make_diffuse_and_glow()
    preview = make_preview(diffuse, glow)

    diffuse.save(OUT / "rustchain_hashcannon_diffuse.tga")
    glow.save(OUT / "rustchain_hashcannon_glow.tga")
    preview.save(OUT / "rustchain_hashcannon_preview.png")


if __name__ == "__main__":
    main()
