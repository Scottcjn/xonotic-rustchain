#!/usr/bin/env python3
"""Generate the RustChain Gas Fee Ghost player-skin texture pack.

The output is deterministic and intentionally self-contained so reviewers can
regenerate the submitted TGA/PNG assets from source.
"""

from pathlib import Path
import math
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "pk3_build" / "models" / "player" / "skins" / "rustchain_gas_fee_ghost"
SIZE = 1024
SEED = 0x474153464545


def font(size: int) -> ImageFont.ImageFont:
    for name in (
        "DejaVuSansMono-Bold.ttf",
        "DejaVuSans-Bold.ttf",
        "arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def clamp(value: int) -> int:
    return max(0, min(255, value))


def add_spectral_noise(image: Image.Image, rng: random.Random) -> None:
    pixels = image.load()
    for y in range(SIZE):
        for x in range(SIZE):
            wave = int(12 * math.sin((x + y) / 38.0) + 9 * math.sin(y / 17.0))
            grain = rng.randrange(-5, 6)
            r, g, b = pixels[x, y]
            pixels[x, y] = (
                clamp(r + wave // 3 + grain),
                clamp(g + wave + grain),
                clamp(b + wave + grain * 2),
            )


def polygon(draw: ImageDraw.ImageDraw, points, fill, outline, width=3) -> None:
    draw.polygon(points, fill=fill)
    draw.line(points + [points[0]], fill=outline, width=width, joint="curve")


def glow_line(diffuse: ImageDraw.ImageDraw, glow: ImageDraw.ImageDraw, points, color, glow_color, width=5) -> None:
    diffuse.line(points, fill=color, width=width, joint="curve")
    diffuse.line(points, fill=(230, 255, 255), width=max(1, width // 3), joint="curve")
    glow.line(points, fill=glow_color, width=width * 3, joint="curve")
    for x, y in points:
        diffuse.ellipse((x - 5, y - 5, x + 5, y + 5), fill=color)
        glow.ellipse((x - 12, y - 12, x + 12, y + 12), fill=glow_color)


def draw_hex(draw: ImageDraw.ImageDraw, center, radius, fill, outline, width=3) -> None:
    cx, cy = center
    pts = []
    for i in range(6):
        a = math.pi / 6 + i * math.pi / 3
        pts.append((cx + math.cos(a) * radius, cy + math.sin(a) * radius))
    draw.polygon(pts, fill=fill)
    draw.line(pts + [pts[0]], fill=outline, width=width, joint="curve")


def make_diffuse_and_glow() -> tuple[Image.Image, Image.Image]:
    rng = random.Random(SEED)
    diffuse = Image.new("RGB", (SIZE, SIZE), (15, 18, 28))
    glow = Image.new("RGB", (SIZE, SIZE), (0, 0, 0))
    add_spectral_noise(diffuse, rng)

    d = ImageDraw.Draw(diffuse)
    g = ImageDraw.Draw(glow)

    cyan = (88, 244, 255)
    ghost = (72, 176, 211)
    violet = (191, 92, 255)
    hot = (255, 80, 184)
    pale = (200, 250, 255)
    armor = (25, 34, 50)
    shadow = (16, 20, 33)

    # UV-friendly spectral armor atlas: hood, torso, arms, legs, side strips.
    plates = [
        [(392, 58), (632, 58), (702, 226), (512, 306), (322, 226)],
        [(294, 326), (730, 326), (672, 678), (512, 754), (352, 678)],
        [(78, 298), (264, 338), (228, 748), (48, 704)],
        [(760, 338), (946, 298), (976, 704), (796, 748)],
        [(330, 752), (496, 790), (454, 966), (286, 966)],
        [(528, 790), (694, 752), (738, 966), (570, 966)],
        [(28, 70), (192, 70), (192, 252), (28, 252)],
        [(832, 70), (996, 70), (996, 252), (832, 252)],
    ]
    fills = [shadow, armor, (22, 29, 44), (22, 29, 44), shadow, shadow, (19, 25, 38), (19, 25, 38)]
    for pts, fill in zip(plates, fills):
        polygon(d, pts, fill, cyan, 3)

    # Translucent ghost veil overlays.
    veil = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    vd = ImageDraw.Draw(veil)
    for offset in range(0, 240, 24):
        pts = []
        for x in range(-40, SIZE + 80, 42):
            y = 120 + offset + int(22 * math.sin((x + offset) / 72.0))
            pts.append((x, y))
        vd.line(pts, fill=(95, 240, 255, 48), width=10)
    diffuse = Image.alpha_composite(diffuse.convert("RGBA"), veil).convert("RGB")
    d = ImageDraw.Draw(diffuse)

    # Gas meter core.
    d.ellipse((444, 424, 580, 560), fill=(15, 38, 54), outline=pale, width=5)
    for i, color in enumerate((cyan, violet, hot)):
        box = (466 + i * 20, 446 + i * 16, 558 - i * 20, 538 - i * 16)
        d.arc(box, start=210, end=24, fill=color, width=8)
        g.arc(box, start=210, end=24, fill=color, width=20)
    d.text((474, 480), "GAS", fill=pale, font=font(31))

    # Floating transaction paths and fee spikes.
    for lane in range(9):
        y = 126 + lane * 90 + rng.randrange(-18, 18)
        points = []
        for step in range(6):
            x = 112 + step * 160 + rng.randrange(-34, 34)
            points.append((x, y + int(32 * math.sin(step + lane))))
        color = cyan if lane % 2 == 0 else violet
        glow_color = (70, 255, 255) if lane % 2 == 0 else (220, 90, 255)
        glow_line(d, g, points, color, glow_color, width=4)

    for _ in range(38):
        x = rng.randrange(70, 954)
        y = rng.randrange(92, 932)
        draw_hex(d, (x, y), rng.randrange(10, 24), (18, 38, 58), rng.choice((cyan, violet, hot)), 2)
        if rng.random() < 0.45:
            draw_hex(g, (x, y), rng.randrange(10, 24), rng.choice(((30, 255, 255), (220, 80, 255), (255, 70, 170))), (0, 0, 0), 1)

    # Transaction numerals and gas fee readouts.
    mono_big = font(50)
    mono = font(28)
    d.text((366, 254), "GAS FEE", fill=pale, font=mono_big)
    d.text((380, 598), "0.000042 RTC", fill=(255, 156, 219), font=mono)
    d.text((70, 266), "wei++", fill=(159, 242, 255), font=mono)
    d.text((812, 266), "gwei", fill=(230, 174, 255), font=mono)
    for _ in range(56):
        x = rng.randrange(42, 920)
        y = rng.randrange(46, 940)
        text = rng.choice(("21", "42", "1559", "0x", "gas", "fee", "base", "tip"))
        fill = rng.choice(((128, 244, 255), (245, 126, 255), (255, 130, 204), (196, 230, 255)))
        d.text((x, y), text, fill=fill, font=mono)
        if rng.random() < 0.55:
            g.text((x, y), text, fill=fill, font=mono)

    # Vapor edge highlights.
    for side in (-1, 1):
        for start_y in (146, 356, 560, 790):
            x0 = 512 + side * rng.randrange(60, 180)
            pts = []
            for step in range(7):
                pts.append((x0 + side * step * rng.randrange(22, 36), start_y + step * rng.randrange(16, 31)))
            glow_line(d, g, pts, (109, 242, 255), (70, 255, 255), width=3)

    glow = glow.filter(ImageFilter.GaussianBlur(2.4))
    return diffuse, glow


def make_preview(diffuse: Image.Image, glow: Image.Image) -> Image.Image:
    canvas = Image.new("RGB", (1400, 760), (12, 14, 24))
    bg = diffuse.resize((760, 760)).filter(ImageFilter.GaussianBlur(6))
    canvas.paste(bg, (0, 0))

    d = ImageDraw.Draw(canvas)
    d.rectangle((0, 0, 1400, 760), outline=(96, 244, 255), width=3)
    d.text((742, 78), "Gas Fee Ghost", fill=(219, 252, 255), font=font(58))
    d.text((744, 146), "RustChain Xonotic skin", fill=(188, 204, 220), font=font(32))
    d.text((744, 214), "Diffuse + glow maps, 1024x1024 TGA", fill=(188, 204, 220), font=font(27))
    d.text((744, 256), "CC-BY-SA-4.0, deterministic procedural source", fill=(188, 204, 220), font=font(27))

    figure = Image.new("RGBA", (440, 540), (0, 0, 0, 0))
    f = ImageDraw.Draw(figure)
    f.ellipse((158, 22, 282, 146), fill=(28, 42, 60, 210), outline=(105, 248, 255), width=5)
    f.polygon([(140, 136), (300, 136), (354, 340), (220, 416), (86, 340)], fill=(24, 34, 52, 220), outline=(105, 248, 255))
    f.polygon([(126, 180), (40, 326), (86, 372), (158, 242)], fill=(20, 28, 46, 190), outline=(196, 90, 255))
    f.polygon([(314, 180), (400, 326), (354, 372), (282, 242)], fill=(20, 28, 46, 190), outline=(255, 90, 184))
    f.polygon([(144, 406), (210, 416), (188, 526), (106, 526)], fill=(18, 26, 43, 190), outline=(105, 248, 255))
    f.polygon([(230, 416), (296, 406), (334, 526), (252, 526)], fill=(18, 26, 43, 190), outline=(105, 248, 255))
    for y in (86, 202, 272, 462):
        f.line((118, y, 318, y + 28), fill=(110, 248, 255, 235), width=5)
    f.ellipse((194, 210, 246, 262), fill=(245, 94, 255, 230))
    f.text((172, 292), "GAS", fill=(230, 255, 255), font=font(34))
    figure = figure.filter(ImageFilter.GaussianBlur(0.2)).resize((340, 417), Image.Resampling.LANCZOS)
    canvas.paste(figure, (850, 316), figure)

    diff_thumb = diffuse.resize((190, 190))
    glow_thumb = glow.resize((190, 190))
    canvas.paste(diff_thumb, (70, 500))
    canvas.paste(glow_thumb, (284, 500))
    d.rectangle((70, 500, 260, 690), outline=(219, 252, 255), width=2)
    d.rectangle((284, 500, 474, 690), outline=(219, 252, 255), width=2)
    d.text((70, 704), "diffuse", fill=(219, 252, 255), font=font(23))
    d.text((284, 704), "glow", fill=(219, 252, 255), font=font(23))
    return canvas


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    diffuse, glow = make_diffuse_and_glow()
    preview = make_preview(diffuse, glow)

    diffuse.save(OUT / "rustchain_gas_fee_ghost_diffuse.tga")
    glow.save(OUT / "rustchain_gas_fee_ghost_glow.tga")
    preview.save(OUT / "rustchain_gas_fee_ghost_preview.png")


if __name__ == "__main__":
    main()
