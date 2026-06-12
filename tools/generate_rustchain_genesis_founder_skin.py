#!/usr/bin/env python3
"""Generate the RustChain Genesis / Founder player-skin texture pack.

The output is deterministic and self-contained so reviewers can regenerate the
submitted TGA/PNG assets from source.
"""

from pathlib import Path
import math
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "pk3_build" / "models" / "player" / "skins" / "rustchain_genesis_founder"
SIZE = 1024
SEED = 0x6E3515F0


def font(size: int) -> ImageFont.ImageFont:
    for name in ("DejaVuSans-Bold.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def clamp(value: int) -> int:
    return max(0, min(255, value))


def add_prestige_microtexture(base: Image.Image) -> None:
    pixels = base.load()
    for y in range(SIZE):
        for x in range(SIZE):
            radial = math.hypot(x - SIZE / 2, y - SIZE / 2) / (SIZE / 2)
            sun = int(18 * max(0, 1 - radial))
            grid = 7 if ((x // 24) + (y // 24)) & 1 else -5
            ripple = int(8 * math.sin((x - y) / 46.0))
            r, g, b = pixels[x, y]
            pixels[x, y] = (clamp(r + sun + grid + ripple), clamp(g + sun + grid), clamp(b + sun - grid))


def polygon(draw: ImageDraw.ImageDraw, points, fill, outline, width=3) -> None:
    draw.polygon(points, fill=fill)
    draw.line(points + [points[0]], fill=outline, width=width, joint="curve")


def draw_circuit_trace(draw: ImageDraw.ImageDraw, glow: ImageDraw.ImageDraw, pts, color, core) -> None:
    draw.line(pts, fill=color, width=5, joint="curve")
    draw.line(pts, fill=core, width=1, joint="curve")
    glow.line(pts, fill=color, width=14, joint="curve")
    for x, y in pts:
        draw.ellipse((x - 9, y - 9, x + 9, y + 9), fill=(22, 23, 25), outline=core, width=2)
        glow.ellipse((x - 13, y - 13, x + 13, y + 13), fill=color)


def draw_laurel(draw: ImageDraw.ImageDraw, glow: ImageDraw.ImageDraw, side: int, color, core) -> None:
    base_x = 512 + side * 245
    for i in range(13):
        y = 178 + i * 42
        curve = int(58 * math.sin(i / 12 * math.pi))
        x = base_x + side * curve
        angle = -24 if side < 0 else 24
        leaf = Image.new("RGBA", (76, 38), (0, 0, 0, 0))
        l = ImageDraw.Draw(leaf)
        l.ellipse((5, 4, 71, 34), fill=color + (255,), outline=core + (255,), width=2)
        leaf = leaf.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
        draw.bitmap((x - leaf.width // 2, y - leaf.height // 2), leaf, fill=color)
        glow.ellipse((x - 34, y - 18, x + 34, y + 18), fill=color)


def make_diffuse_and_glow() -> tuple[Image.Image, Image.Image]:
    rng = random.Random(SEED)
    diffuse = Image.new("RGB", (SIZE, SIZE), (24, 23, 25))
    glow = Image.new("RGB", (SIZE, SIZE), (0, 0, 0))
    add_prestige_microtexture(diffuse)

    d = ImageDraw.Draw(diffuse)
    g = ImageDraw.Draw(glow)

    gold = (255, 205, 74)
    gold_core = (255, 244, 194)
    amber = (255, 145, 42)
    ivory = (238, 236, 214)
    obsidian = (27, 27, 31)
    deep = (39, 35, 38)
    bronze = (138, 83, 38)

    # Prestige armor plates with founder-gold trim.
    plates = [
        [(356, 60), (668, 60), (714, 268), (512, 338), (310, 268)],
        [(292, 344), (732, 344), (692, 718), (512, 794), (332, 718)],
        [(70, 300), (264, 350), (220, 744), (44, 690)],
        [(760, 350), (954, 300), (980, 690), (804, 744)],
        [(316, 770), (498, 812), (454, 970), (280, 970)],
        [(526, 812), (708, 770), (744, 970), (570, 970)],
        [(28, 74), (196, 74), (196, 244), (28, 244)],
        [(828, 74), (996, 74), (996, 244), (828, 244)],
    ]
    for index, pts in enumerate(plates):
        fill = deep if index in (0, 1) else obsidian
        outline = gold if index % 2 == 0 else ivory
        polygon(d, pts, fill, outline, width=4)

    # Genesis block chest medallion.
    d.rounded_rectangle((400, 410, 624, 586), radius=28, fill=(34, 32, 34), outline=gold_core, width=5)
    d.rounded_rectangle((430, 440, 594, 556), radius=18, fill=(71, 47, 28), outline=gold, width=4)
    g.rounded_rectangle((384, 394, 640, 602), radius=36, fill=(214, 139, 28))
    d.text((456, 456), "BLOCK", fill=gold_core, font=font(30))
    d.text((478, 494), "0000", fill=(255, 231, 139), font=font(36))
    d.text((458, 536), "GENESIS", fill=ivory, font=font(22))

    # Crown crest and founding chain halo.
    crown = [(418, 186), (456, 120), (498, 180), (512, 104), (530, 180), (568, 120), (606, 186)]
    polygon(d, crown, bronze, gold_core, width=4)
    g.line(crown + [crown[0]], fill=gold, width=14, joint="curve")
    for radius in (118, 162, 206):
        box = (512 - radius, 246 - radius // 2, 512 + radius, 246 + radius // 2)
        d.ellipse(box, outline=gold, width=3)
        g.ellipse(box, outline=gold, width=9)

    draw_laurel(d, g, -1, gold, gold_core)
    draw_laurel(d, g, 1, gold, gold_core)

    # Founding ledger traces radiate from the medallion.
    for angle in range(0, 360, 30):
        pts = []
        for step in range(5):
            radius = 112 + step * 82
            bend = 0.12 * math.sin(step * 1.7 + angle)
            x = int(512 + math.cos(math.radians(angle) + bend) * radius)
            y = int(500 + math.sin(math.radians(angle) + bend) * radius * 0.78)
            pts.append((x, y))
        draw_circuit_trace(d, g, pts, gold if angle % 60 == 0 else amber, gold_core)

    # Hash fragments and founder markings.
    hex_chars = "0123456789abcdef"
    for _ in range(70):
        x = rng.randrange(44, SIZE - 150)
        y = rng.randrange(38, SIZE - 38)
        text = "".join(rng.choice(hex_chars) for _ in range(8))
        color = (
            rng.randrange(142, 228),
            rng.randrange(106, 178),
            rng.randrange(50, 96),
        )
        d.text((x, y), text, fill=color, font=font(17))

    d.text((330, 286), "GENESIS", fill=gold_core, font=font(60))
    d.text((390, 628), "FOUNDER", fill=ivory, font=font(44))
    d.text((86, 254), "epoch 0", fill=(255, 224, 144), font=font(30))
    d.text((812, 254), "root", fill=(255, 224, 144), font=font(30))

    for _ in range(240):
        x = rng.randrange(SIZE)
        y = rng.randrange(SIZE)
        side = rng.randrange(2, 7)
        if rng.random() < 0.72:
            color = (rng.randrange(42, 82), rng.randrange(36, 64), rng.randrange(30, 48))
        else:
            color = (rng.randrange(130, 210), rng.randrange(88, 150), rng.randrange(36, 72))
        d.rectangle((x, y, x + side, y + side), fill=color)

    # Subtle white-gold origin star over the heart.
    star = []
    for i in range(16):
        radius = 86 if i % 2 == 0 else 34
        angle = math.radians(-90 + i * 22.5)
        star.append((int(512 + radius * math.cos(angle)), int(500 + radius * math.sin(angle))))
    d.line(star + [star[0]], fill=gold_core, width=3, joint="curve")
    g.line(star + [star[0]], fill=gold, width=10, joint="curve")

    glow = glow.filter(ImageFilter.GaussianBlur(2.1))
    return diffuse, glow


def make_preview(diffuse: Image.Image, glow: Image.Image) -> Image.Image:
    canvas = Image.new("RGB", (1400, 760), (19, 18, 20))
    bg = diffuse.resize((700, 700)).filter(ImageFilter.GaussianBlur(4))
    canvas.paste(bg, (0, 30))

    d = ImageDraw.Draw(canvas)
    gold = (255, 205, 74)
    ivory = (238, 236, 214)
    d.rectangle((0, 0, 1400, 760), outline=gold, width=3)
    d.text((760, 70), "RustChain Genesis", fill=ivory, font=font(50))
    d.text((762, 132), "Founder prestige skin", fill=(255, 226, 148), font=font(34))
    d.text((762, 198), "Gold-accent armor with origin-block glow", fill=(204, 196, 176), font=font(28))
    d.text((762, 242), "Diffuse + glow maps, 1024x1024 TGA", fill=(204, 196, 176), font=font(28))
    d.text((762, 286), "CC-BY-SA-4.0, deterministic procedural source", fill=(204, 196, 176), font=font(28))

    avatar = Image.new("RGBA", (420, 520), (0, 0, 0, 0))
    a = ImageDraw.Draw(avatar)
    a.ellipse((156, 20, 264, 128), fill=(42, 38, 38), outline=gold, width=5)
    a.polygon([(160, 42), (184, 0), (210, 40), (230, 0), (260, 42)], fill=(138, 83, 38), outline=(255, 244, 194))
    a.rounded_rectangle((112, 128, 308, 320), radius=34, fill=(42, 38, 39), outline=gold, width=5)
    a.rounded_rectangle((154, 180, 266, 264), radius=18, fill=(75, 48, 28), outline=(255, 244, 194), width=4)
    a.text((172, 202), "0000", fill=(255, 244, 194), font=font(30))
    a.polygon([(112, 164), (34, 292), (78, 326), (140, 220)], fill=(36, 32, 34), outline=gold)
    a.polygon([(308, 164), (388, 292), (342, 326), (280, 220)], fill=(36, 32, 34), outline=gold)
    a.polygon([(146, 320), (210, 320), (190, 505), (112, 505)], fill=(30, 29, 31), outline=gold)
    a.polygon([(210, 320), (276, 320), (308, 505), (230, 505)], fill=(30, 29, 31), outline=gold)
    for y in (86, 178, 238, 390):
        a.line((118, y, 302, y - 12), fill=gold, width=5)
    for side in (-1, 1):
        for i in range(8):
            y = 178 + i * 28
            x = 210 + side * (94 + i * 6)
            a.ellipse((x - 18, y - 9, x + 18, y + 9), fill=gold, outline=(255, 244, 194))
    avatar = avatar.resize((340, 421), Image.Resampling.LANCZOS)
    canvas.paste(avatar, (850, 318), avatar)

    diff_thumb = diffuse.resize((190, 190))
    glow_thumb = glow.resize((190, 190))
    canvas.paste(diff_thumb, (70, 500))
    canvas.paste(glow_thumb, (284, 500))
    d.rectangle((70, 500, 260, 690), outline=ivory, width=2)
    d.rectangle((284, 500, 474, 690), outline=ivory, width=2)
    d.text((70, 704), "diffuse", fill=ivory, font=font(23))
    d.text((284, 704), "glow", fill=ivory, font=font(23))
    return canvas


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    diffuse, glow = make_diffuse_and_glow()
    preview = make_preview(diffuse, glow)

    diffuse.save(OUT / "rustchain_genesis_founder_diffuse.tga")
    glow.save(OUT / "rustchain_genesis_founder_glow.tga")
    preview.save(OUT / "rustchain_genesis_founder_preview.png")


if __name__ == "__main__":
    main()
