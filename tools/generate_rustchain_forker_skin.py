#!/usr/bin/env python3
"""Generate the RustChain Forker player-skin texture pack.

The output is deterministic and self-contained so reviewers can regenerate the
submitted TGA/PNG assets from source.
"""

from pathlib import Path
import math
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "pk3_build" / "models" / "player" / "skins" / "rustchain_forker"
SIZE = 1024
SEED = 0xF0422026


def font(size: int) -> ImageFont.ImageFont:
    for name in ("DejaVuSans-Bold.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def clamp(value: int) -> int:
    return max(0, min(255, value))


def add_microtexture(base: Image.Image) -> None:
    pixels = base.load()
    for y in range(SIZE):
        for x in range(SIZE):
            left_side = x < SIZE // 2
            cell = ((x // 18) ^ (y // 18)) & 1
            diagonal = ((x + y) // 33) & 1
            delta = 11 if cell == diagonal else -5
            if not left_side:
                delta = -delta
            r, g, b = pixels[x, y]
            pixels[x, y] = (clamp(r + delta), clamp(g + delta), clamp(b + delta))


def polygon(draw: ImageDraw.ImageDraw, points, fill, outline, width=3) -> None:
    draw.polygon(points, fill=fill)
    draw.line(points + [points[0]], fill=outline, width=width, joint="curve")


def trace(draw: ImageDraw.ImageDraw, glow: ImageDraw.ImageDraw, pts, color, core) -> None:
    draw.line(pts, fill=color, width=5, joint="curve")
    draw.line(pts, fill=core, width=1, joint="curve")
    glow.line(pts, fill=color, width=12, joint="curve")
    for x, y in pts:
        draw.ellipse((x - 8, y - 8, x + 8, y + 8), fill=(18, 22, 30), outline=core, width=2)
        glow.ellipse((x - 12, y - 12, x + 12, y + 12), fill=color)


def draw_fork_crack(draw: ImageDraw.ImageDraw, glow: ImageDraw.ImageDraw) -> None:
    crack = [
        (512, 30),
        (491, 118),
        (530, 204),
        (506, 306),
        (536, 410),
        (494, 524),
        (527, 650),
        (504, 786),
        (520, 994),
    ]
    draw.line(crack, fill=(236, 246, 255), width=8, joint="curve")
    draw.line(crack, fill=(28, 31, 41), width=3, joint="curve")
    glow.line(crack, fill=(188, 244, 255), width=18, joint="curve")
    branch_left = [(506, 306), (404, 360), (350, 454)]
    branch_right = [(536, 410), (652, 474), (708, 588)]
    branch_lower = [(494, 524), (398, 610), (330, 720)]
    for branch in (branch_left, branch_right, branch_lower):
        draw.line(branch, fill=(236, 246, 255), width=6, joint="curve")
        draw.line(branch, fill=(28, 31, 41), width=2, joint="curve")
        glow.line(branch, fill=(188, 244, 255), width=14, joint="curve")


def make_diffuse_and_glow() -> tuple[Image.Image, Image.Image]:
    rng = random.Random(SEED)
    diffuse = Image.new("RGB", (SIZE, SIZE), (20, 22, 29))
    glow = Image.new("RGB", (SIZE, SIZE), (0, 0, 0))
    add_microtexture(diffuse)

    d = ImageDraw.Draw(diffuse)
    g = ImageDraw.Draw(glow)

    # Split-fork armor palette: cold canonical side versus hot rebel side.
    cold = (25, 83, 111)
    cold_dark = (21, 40, 56)
    cold_glow = (50, 224, 255)
    warm = (118, 49, 36)
    warm_dark = (55, 31, 31)
    warm_glow = (255, 113, 58)
    neutral = (35, 40, 48)
    silver = (190, 207, 214)

    left_plates = [
        [(332, 70), (512, 46), (488, 284), (336, 246)],
        [(272, 326), (512, 306), (490, 734), (320, 686)],
        [(64, 310), (252, 348), (214, 742), (48, 682)],
        [(310, 748), (488, 784), (444, 968), (282, 968)],
        [(24, 82), (184, 82), (184, 248), (24, 248)],
    ]
    right_plates = [
        [(512, 46), (692, 70), (688, 246), (536, 284)],
        [(512, 306), (752, 326), (704, 686), (534, 734)],
        [(772, 348), (960, 310), (976, 682), (810, 742)],
        [(536, 784), (714, 748), (742, 968), (580, 968)],
        [(840, 82), (1000, 82), (1000, 248), (840, 248)],
    ]
    for pts in left_plates:
        polygon(d, pts, cold_dark, cold_glow)
    for pts in right_plates:
        polygon(d, pts, warm_dark, warm_glow)

    core = [(426, 424), (512, 368), (598, 424), (578, 548), (512, 594), (446, 548)]
    polygon(d, core, neutral, silver, width=4)
    d.polygon([(426, 424), (512, 368), (512, 594), (446, 548)], fill=cold)
    d.polygon([(512, 368), (598, 424), (578, 548), (512, 594)], fill=warm)
    d.line(core + [core[0]], fill=silver, width=4)
    g.polygon(core, fill=(124, 194, 170))

    draw_fork_crack(d, g)

    # Mirrored but divergent chain traces emphasize chain split.
    for side, color, core_color in (
        (-1, cold_glow, (206, 250, 255)),
        (1, warm_glow, (255, 221, 196)),
    ):
        for y in (146, 382, 512, 662, 840):
            x0 = 512 + side * rng.randint(46, 120)
            pts = [(x0, y)]
            for _ in range(4):
                last_x, last_y = pts[-1]
                pts.append((last_x + side * rng.randint(44, 98), last_y + rng.randint(-34, 48)))
            trace(d, g, pts, color, core_color)

    label_font = font(58)
    small_font = font(30)
    d.text((350, 248), "FORKER", fill=(230, 246, 250), font=label_font)
    d.text((100, 258), "canonical", fill=(188, 238, 250), font=small_font)
    d.text((812, 258), "reorg", fill=(255, 209, 184), font=small_font)
    d.text((376, 630), "split", fill=(215, 232, 236), font=small_font)
    d.text((530, 630), "chain", fill=(255, 208, 182), font=small_font)

    for _ in range(210):
        x = rng.randrange(SIZE)
        y = rng.randrange(SIZE)
        radius = rng.randrange(2, 7)
        if x < SIZE // 2:
            color = (rng.randrange(28, 54), rng.randrange(80, 118), rng.randrange(104, 150))
        else:
            color = (rng.randrange(102, 150), rng.randrange(46, 76), rng.randrange(34, 52))
        d.rectangle((x, y, x + radius, y + radius), fill=color)

    # Add short hash fragments along the split.
    for index in range(22):
        y = 86 + index * 40
        drift = int(22 * math.sin(index * 1.17))
        x = 492 + drift
        d.line((x, y, x + 44, y + 18), fill=(228, 243, 247), width=2)
        g.line((x, y, x + 44, y + 18), fill=(188, 244, 255), width=5)

    glow = glow.filter(ImageFilter.GaussianBlur(2.2))
    return diffuse, glow


def make_preview(diffuse: Image.Image, glow: Image.Image) -> Image.Image:
    canvas = Image.new("RGB", (1400, 760), (17, 19, 24))
    left = diffuse.crop((0, 0, SIZE // 2, SIZE)).resize((350, 700))
    right = diffuse.crop((SIZE // 2, 0, SIZE, SIZE)).resize((350, 700))
    canvas.paste(left.filter(ImageFilter.GaussianBlur(3)), (0, 30))
    canvas.paste(right.filter(ImageFilter.GaussianBlur(3)), (350, 30))

    d = ImageDraw.Draw(canvas)
    d.rectangle((0, 0, 1400, 760), outline=(188, 244, 255), width=3)
    d.line((700, 0, 700, 760), fill=(255, 113, 58), width=3)
    d.text((760, 86), "RustChain Forker", fill=(231, 246, 250), font=font(58))
    d.text((762, 160), "Dual-tone split-chain player skin", fill=(188, 202, 208), font=font(31))
    d.text((762, 224), "Diffuse + glow maps, 1024x1024 TGA", fill=(188, 202, 208), font=font(28))
    d.text((762, 268), "CC-BY-SA-4.0, deterministic procedural source", fill=(188, 202, 208), font=font(28))

    avatar = Image.new("RGBA", (420, 520), (0, 0, 0, 0))
    a = ImageDraw.Draw(avatar)
    cold = (24, 82, 112)
    warm = (126, 52, 36)
    a.ellipse((156, 20, 264, 128), fill=(36, 44, 54), outline=(214, 236, 242), width=5)
    a.pieslice((156, 20, 264, 128), 90, 270, fill=cold)
    a.pieslice((156, 20, 264, 128), -90, 90, fill=warm)
    a.rounded_rectangle((116, 128, 304, 322), radius=34, fill=(38, 43, 52), outline=(214, 236, 242), width=5)
    a.rectangle((116, 128, 210, 322), fill=cold)
    a.rectangle((210, 128, 304, 322), fill=warm)
    a.polygon([(116, 160), (34, 292), (78, 328), (142, 218)], fill=(22, 58, 82), outline=(50, 224, 255))
    a.polygon([(304, 160), (386, 292), (342, 328), (278, 218)], fill=(96, 42, 33), outline=(255, 113, 58))
    a.polygon([(145, 322), (210, 322), (190, 505), (112, 505)], fill=(21, 55, 78), outline=(50, 224, 255))
    a.polygon([(210, 322), (275, 322), (308, 505), (230, 505)], fill=(92, 40, 32), outline=(255, 113, 58))
    a.line((210, 30, 198, 502), fill=(232, 246, 250), width=6)
    for y in (84, 182, 242, 390):
        a.line((118, y, 202, y + 24), fill=(50, 224, 255), width=5)
        a.line((218, y + 18, 302, y - 8), fill=(255, 113, 58), width=5)
    avatar = avatar.resize((340, 421), Image.Resampling.LANCZOS)
    canvas.paste(avatar, (850, 318), avatar)

    diff_thumb = diffuse.resize((190, 190))
    glow_thumb = glow.resize((190, 190))
    canvas.paste(diff_thumb, (70, 500))
    canvas.paste(glow_thumb, (284, 500))
    d.rectangle((70, 500, 260, 690), outline=(231, 246, 250), width=2)
    d.rectangle((284, 500, 474, 690), outline=(231, 246, 250), width=2)
    d.text((70, 704), "diffuse", fill=(231, 246, 250), font=font(23))
    d.text((284, 704), "glow", fill=(231, 246, 250), font=font(23))
    return canvas


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    diffuse, glow = make_diffuse_and_glow()
    preview = make_preview(diffuse, glow)

    diffuse.save(OUT / "rustchain_forker_diffuse.tga")
    glow.save(OUT / "rustchain_forker_glow.tga")
    preview.save(OUT / "rustchain_forker_preview.png")


if __name__ == "__main__":
    main()
