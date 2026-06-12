#!/usr/bin/env python3
"""Generate the RustChain Validator player-skin texture pack.

The output is deterministic and intentionally self-contained so reviewers can
regenerate the submitted TGA/PNG assets from source.
"""

from pathlib import Path
import math
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "pk3_build" / "models" / "player" / "skins" / "rustchain_validator"
SIZE = 1024
SEED = 0x5254432026


def font(size: int) -> ImageFont.ImageFont:
    for name in ("DejaVuSans-Bold.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def panel(draw: ImageDraw.ImageDraw, points, fill, outline, width=3):
    draw.polygon(points, fill=fill)
    draw.line(points + [points[0]], fill=outline, width=width, joint="curve")


def add_carbon(base: Image.Image):
    pixels = base.load()
    for y in range(SIZE):
        for x in range(SIZE):
            stripe = ((x // 16) + (y // 16)) % 2
            diag = ((x + y) // 24) % 2
            delta = 10 if stripe == diag else -4
            r, g, b = pixels[x, y]
            pixels[x, y] = (
                max(0, min(255, r + delta)),
                max(0, min(255, g + delta)),
                max(0, min(255, b + delta)),
            )


def circuit_path(draw: ImageDraw.ImageDraw, glow: ImageDraw.ImageDraw, pts):
    draw.line(pts, fill=(35, 224, 122), width=5, joint="curve")
    draw.line(pts, fill=(183, 255, 214), width=1, joint="curve")
    glow.line(pts, fill=(38, 255, 128), width=10, joint="curve")
    for x, y in pts:
        draw.ellipse((x - 8, y - 8, x + 8, y + 8), fill=(16, 87, 50), outline=(158, 255, 201), width=2)
        glow.ellipse((x - 11, y - 11, x + 11, y + 11), fill=(44, 255, 132))


def make_diffuse_and_glow():
    rng = random.Random(SEED)
    diffuse = Image.new("RGB", (SIZE, SIZE), (21, 25, 29))
    glow = Image.new("RGB", (SIZE, SIZE), (0, 0, 0))
    add_carbon(diffuse)

    d = ImageDraw.Draw(diffuse)
    g = ImageDraw.Draw(glow)

    # Symmetric armor plates laid out as a UV-friendly atlas: head, torso, arms,
    # legs, and side strips. The pattern is decorative but not model-specific.
    outline = (22, 235, 123)
    dark = (35, 41, 48)
    mid = (54, 64, 72)
    gold = (207, 159, 55)

    plates = [
        [(390, 64), (634, 64), (684, 230), (512, 304), (340, 230)],
        [(300, 330), (724, 330), (666, 670), (512, 746), (358, 670)],
        [(84, 310), (262, 340), (220, 740), (56, 694)],
        [(762, 340), (940, 310), (968, 694), (804, 740)],
        [(338, 746), (498, 782), (456, 960), (294, 960)],
        [(526, 782), (686, 746), (730, 960), (568, 960)],
        [(24, 72), (188, 72), (188, 248), (24, 248)],
        [(836, 72), (1000, 72), (1000, 248), (836, 248)],
    ]
    fills = [mid, dark, (42, 49, 55), (42, 49, 55), dark, dark, (31, 36, 42), (31, 36, 42)]
    for pts, fill in zip(plates, fills):
        panel(d, pts, fill, outline)

    # Bright validator core.
    d.ellipse((452, 430, 572, 550), fill=(10, 48, 32), outline=(173, 255, 198), width=5)
    d.ellipse((482, 460, 542, 520), fill=(44, 244, 126))
    g.ellipse((438, 416, 586, 564), fill=(28, 255, 124))

    # Circuit traces with mirrored structure.
    for side in (-1, 1):
        for y in (146, 400, 520, 642, 842):
            x0 = 512 + side * rng.randint(32, 110)
            pts = [(x0, y)]
            for _ in range(4):
                last_x, last_y = pts[-1]
                pts.append((last_x + side * rng.randint(38, 95), last_y + rng.randint(-28, 46)))
            circuit_path(d, g, pts)

    for x in (128, 896, 382, 642):
        for y in range(150, 900, 120):
            if rng.random() < 0.75:
                circuit_path(d, g, [(x, y), (x + rng.randint(-40, 40), y + 46), (x, y + 86)])

    # Validator text and hash marks.
    title_font = font(58)
    small_font = font(30)
    d.text((358, 250), "VALIDATOR", fill=(199, 255, 220), font=title_font)
    d.text((404, 586), "RTC", fill=gold, font=title_font)
    d.text((382, 660), "0x525443", fill=(175, 218, 192), font=small_font)
    d.text((62, 258), "stake", fill=(164, 220, 184), font=small_font)
    d.text((826, 258), "finalize", fill=(164, 220, 184), font=small_font)

    for _ in range(180):
        x = rng.randrange(SIZE)
        y = rng.randrange(SIZE)
        a = rng.randrange(3, 9)
        color = (rng.randrange(55, 90), rng.randrange(68, 92), rng.randrange(74, 104))
        d.rectangle((x, y, x + a, y + a), fill=color)

    glow = glow.filter(ImageFilter.GaussianBlur(2.2))
    return diffuse, glow


def make_preview(diffuse: Image.Image, glow: Image.Image):
    canvas = Image.new("RGB", (1400, 760), (18, 20, 23))
    bg = diffuse.resize((700, 700)).filter(ImageFilter.GaussianBlur(5))
    canvas.paste(bg, (0, 30))

    d = ImageDraw.Draw(canvas)
    d.rectangle((0, 0, 1400, 760), outline=(38, 255, 128), width=3)
    d.text((760, 92), "RustChain Validator", fill=(207, 255, 224), font=font(58))
    d.text((762, 166), "Xonotic player skin texture pack", fill=(176, 190, 185), font=font(31))
    d.text((762, 232), "Diffuse + glow maps, 1024x1024 TGA", fill=(176, 190, 185), font=font(28))
    d.text((762, 276), "CC-BY-SA-4.0, deterministic procedural source", fill=(176, 190, 185), font=font(28))

    avatar = Image.new("RGBA", (420, 520), (0, 0, 0, 0))
    a = ImageDraw.Draw(avatar)
    a.ellipse((156, 20, 264, 128), fill=(42, 52, 60), outline=(36, 245, 130), width=5)
    a.rounded_rectangle((116, 128, 304, 322), radius=36, fill=(40, 48, 55), outline=(36, 245, 130), width=5)
    a.polygon([(116, 160), (34, 292), (78, 328), (142, 218)], fill=(34, 42, 49), outline=(36, 245, 130))
    a.polygon([(304, 160), (386, 292), (342, 328), (278, 218)], fill=(34, 42, 49), outline=(36, 245, 130))
    a.polygon([(145, 322), (210, 322), (190, 505), (112, 505)], fill=(34, 42, 49), outline=(36, 245, 130))
    a.polygon([(210, 322), (275, 322), (308, 505), (230, 505)], fill=(34, 42, 49), outline=(36, 245, 130))
    for y in (84, 184, 240, 390):
        a.line((122, y, 298, y + 24), fill=(42, 255, 139), width=5)
    a.ellipse((190, 195, 230, 235), fill=(42, 255, 139))
    avatar = avatar.resize((340, 421), Image.Resampling.LANCZOS)
    canvas.paste(avatar, (850, 318), avatar)

    glow_thumb = glow.resize((190, 190))
    diff_thumb = diffuse.resize((190, 190))
    canvas.paste(diff_thumb, (70, 500))
    canvas.paste(glow_thumb, (284, 500))
    d.rectangle((70, 500, 260, 690), outline=(207, 255, 224), width=2)
    d.rectangle((284, 500, 474, 690), outline=(207, 255, 224), width=2)
    d.text((70, 704), "diffuse", fill=(207, 255, 224), font=font(23))
    d.text((284, 704), "glow", fill=(207, 255, 224), font=font(23))
    return canvas


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    diffuse, glow = make_diffuse_and_glow()
    preview = make_preview(diffuse, glow)

    diffuse.save(OUT / "rustchain_validator_diffuse.tga")
    glow.save(OUT / "rustchain_validator_glow.tga")
    preview.save(OUT / "rustchain_validator_preview.png")


if __name__ == "__main__":
    main()
