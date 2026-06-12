#!/usr/bin/env python3
"""Generate the RustChain Double Spend player-skin texture pack.

The output is deterministic and self-contained so reviewers can regenerate the
submitted TGA/PNG assets from source.
"""

from pathlib import Path
import math
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "pk3_build" / "models" / "player" / "skins" / "rustchain_double_spend"
SIZE = 1024
SEED = 0xD0B1E5F3


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


def add_glitch_field(base: Image.Image, rng: random.Random) -> None:
    pixels = base.load()
    for y in range(SIZE):
        row_shift = int(10 * math.sin(y / 19.0) + 5 * math.sin(y / 7.0))
        for x in range(SIZE):
            checker = ((x // 18) ^ (y // 18)) & 1
            tear = 16 if (y + row_shift) % 113 < 5 else 0
            noise = rng.randrange(-5, 6)
            r, g, b = pixels[x, y]
            pixels[x, y] = (
                clamp(r + (9 if checker else -4) + tear + noise),
                clamp(g + (5 if checker else -3) + noise),
                clamp(b + (10 if checker else -5) - tear // 3 + noise),
            )


def polygon(draw: ImageDraw.ImageDraw, points, fill, outline, width=3) -> None:
    draw.polygon(points, fill=fill)
    draw.line(points + [points[0]], fill=outline, width=width, joint="curve")


def glow_poly(draw: ImageDraw.ImageDraw, glow: ImageDraw.ImageDraw, points, fill, outline, glow_color) -> None:
    polygon(draw, points, fill, outline, width=4)
    glow.line(points + [points[0]], fill=glow_color, width=11, joint="curve")


def glow_line(draw: ImageDraw.ImageDraw, glow: ImageDraw.ImageDraw, points, color, glow_color, width=5) -> None:
    draw.line(points, fill=color, width=width, joint="curve")
    draw.line(points, fill=(238, 248, 255), width=max(1, width // 3), joint="curve")
    glow.line(points, fill=glow_color, width=width * 3, joint="curve")


def draw_duplicate_ribbons(draw: ImageDraw.ImageDraw, glow: ImageDraw.ImageDraw, rng: random.Random) -> None:
    cyan = (74, 232, 255)
    red = (255, 82, 104)
    gold = (255, 206, 84)
    for lane in range(11):
        y = 92 + lane * 82 + rng.randrange(-16, 16)
        left = []
        right = []
        for step in range(7):
            x = 58 + step * 82
            left.append((x, y + int(20 * math.sin(step * 0.8 + lane))))
            right.append((SIZE - x, y + int(20 * math.sin(step * 0.8 + lane + 1.4))))
        glow_line(draw, glow, left, cyan, (42, 226, 255), width=4)
        glow_line(draw, glow, right, red, (255, 64, 88), width=4)
        if lane % 3 == 0:
            bridge = [(left[-1][0], left[-1][1]), (512, y + rng.randrange(-28, 28)), (right[-1][0], right[-1][1])]
            glow_line(draw, glow, bridge, gold, (255, 196, 54), width=3)


def draw_packet(draw: ImageDraw.ImageDraw, glow: ImageDraw.ImageDraw, box, label, color, glow_color) -> None:
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=14, fill=(20, 25, 34), outline=color, width=3)
    glow.rounded_rectangle((x0 - 3, y0 - 3, x1 + 3, y1 + 3), radius=18, outline=glow_color, width=8)
    draw.text((x0 + 14, y0 + 10), label, fill=(235, 246, 255), font=font(20))
    draw.line((x0 + 12, y1 - 18, x1 - 12, y1 - 18), fill=color, width=3)
    draw.text((x0 + 14, y1 - 46), "same input", fill=color, font=font(17))


def make_diffuse_and_glow() -> tuple[Image.Image, Image.Image]:
    rng = random.Random(SEED)
    diffuse = Image.new("RGB", (SIZE, SIZE), (18, 20, 30))
    glow = Image.new("RGB", (SIZE, SIZE), (0, 0, 0))
    add_glitch_field(diffuse, rng)

    d = ImageDraw.Draw(diffuse)
    g = ImageDraw.Draw(glow)

    cyan = (72, 232, 255)
    cyan_dark = (24, 54, 70)
    cyan_glow = (36, 220, 255)
    red = (255, 78, 104)
    red_dark = (66, 25, 35)
    red_glow = (255, 58, 88)
    gold = (255, 206, 76)
    cream = (236, 246, 255)
    shadow = (22, 27, 38)
    steel = (40, 48, 61)

    # Split duplicate armor atlas: cool left spend, hot right spend, disputed center.
    left_plates = [
        [(326, 62), (512, 62), (512, 322), (340, 250)],
        [(288, 338), (512, 338), (512, 776), (336, 704)],
        [(70, 320), (266, 356), (224, 736), (48, 682)],
        [(318, 770), (500, 804), (454, 972), (282, 972)],
        [(24, 86), (188, 86), (188, 250), (24, 250)],
    ]
    right_plates = [
        [(512, 62), (698, 62), (684, 250), (512, 322)],
        [(512, 338), (736, 338), (688, 704), (512, 776)],
        [(758, 356), (954, 320), (978, 682), (800, 736)],
        [(524, 804), (706, 770), (742, 972), (570, 972)],
        [(836, 86), (1000, 86), (1000, 250), (836, 250)],
    ]
    for pts in left_plates:
        glow_poly(d, g, pts, cyan_dark, cyan, cyan_glow)
    for pts in right_plates:
        glow_poly(d, g, pts, red_dark, red, red_glow)

    center_plate = [(438, 346), (586, 346), (640, 608), (512, 732), (384, 608)]
    glow_poly(d, g, center_plate, steel, gold, (255, 194, 54))
    d.line((512, 42, 512, 972), fill=(238, 238, 248), width=4)
    g.line((512, 42, 512, 972), fill=(255, 238, 160), width=12)

    # Offset silhouettes: the same spend appears twice, slightly out of phase.
    for offset, color, glow_color, side in ((-30, cyan, cyan_glow, -1), (30, red, red_glow, 1)):
        body = [(512 + offset, 214), (598 + offset, 364), (566 + offset, 604), (512 + offset, 684), (458 + offset, 604), (426 + offset, 364)]
        d.line(body + [body[0]], fill=color, width=5, joint="curve")
        g.line(body + [body[0]], fill=glow_color, width=14, joint="curve")
        d.ellipse((468 + offset, 96, 556 + offset, 184), outline=color, width=5)
        g.ellipse((462 + offset, 90, 562 + offset, 190), outline=glow_color, width=12)
        for y in (272, 412, 552):
            d.line((512 + offset, y, 512 + offset + side * 128, y + 38), fill=color, width=5)
            g.line((512 + offset, y, 512 + offset + side * 128, y + 38), fill=glow_color, width=12)

    draw_duplicate_ribbons(d, g, rng)

    # Conflicting packets and hash fragments.
    draw_packet(d, g, (62, 628, 288, 748), "TX-A", cyan, cyan_glow)
    draw_packet(d, g, (736, 628, 962, 748), "TX-B", red, red_glow)
    draw_packet(d, g, (400, 782, 624, 910), "REORG?", gold, (255, 194, 54))

    title_font = font(52)
    small = font(27)
    tiny = font(18)
    d.text((304, 254), "DOUBLE SPEND", fill=cream, font=title_font)
    d.text((382, 566), "INPUT #42", fill=gold, font=small)
    d.text((66, 260), "left fork", fill=(178, 246, 255), font=small)
    d.text((806, 260), "right fork", fill=(255, 190, 202), font=small)

    for _ in range(72):
        x = rng.randrange(36, SIZE - 150)
        y = rng.randrange(38, SIZE - 36)
        tag = rng.choice(("0x", "UTXO", "dup", "nonce", "race", "fork", "2x", "replay"))
        color = rng.choice((cyan, red, gold, (184, 206, 230)))
        d.text((x, y), tag, fill=color, font=tiny)
        if rng.random() < 0.55:
            g.text((x, y), tag, fill=color, font=tiny)

    # Scanline tears and duplicate offsets.
    for _ in range(32):
        y = rng.randrange(48, 960)
        length = rng.randrange(80, 240)
        x = rng.randrange(20, SIZE - length - 20)
        color = rng.choice((cyan, red, gold))
        d.rectangle((x, y, x + length, y + rng.randrange(3, 8)), fill=color)
        g.rectangle((x, y, x + length, y + 10), fill=color)

    for _ in range(230):
        x = rng.randrange(SIZE)
        y = rng.randrange(SIZE)
        side = rng.randrange(3, 9)
        color = (
            rng.randrange(36, 92),
            rng.randrange(42, 112),
            rng.randrange(54, 130),
        )
        d.rectangle((x, y, x + side, y + side), fill=color)

    glow = glow.filter(ImageFilter.GaussianBlur(2.0))
    return diffuse, glow


def make_preview(diffuse: Image.Image, glow: Image.Image) -> Image.Image:
    canvas = Image.new("RGB", (1400, 760), (15, 17, 24))
    bg = diffuse.resize((720, 720)).filter(ImageFilter.GaussianBlur(4))
    canvas.paste(bg, (0, 20))

    d = ImageDraw.Draw(canvas)
    cyan = (72, 232, 255)
    red = (255, 78, 104)
    gold = (255, 206, 76)
    cream = (236, 246, 255)
    d.rectangle((0, 0, 1400, 760), outline=gold, width=3)
    d.text((758, 82), "RustChain Double Spend", fill=cream, font=font(48))
    d.text((760, 154), "Twin-glitch player skin", fill=(190, 204, 218), font=font(31))
    d.text((760, 218), "Diffuse + glow maps, 1024x1024 TGA", fill=(190, 204, 218), font=font(28))
    d.text((760, 262), "CC-BY-SA-4.0, deterministic procedural source", fill=(190, 204, 218), font=font(28))

    avatar = Image.new("RGBA", (450, 540), (0, 0, 0, 0))
    a = ImageDraw.Draw(avatar)
    for offset, color in ((-28, cyan), (28, red)):
        a.ellipse((170 + offset, 20, 282 + offset, 132), fill=(32, 42, 55, 220), outline=color, width=5)
        a.rounded_rectangle((130 + offset, 128, 322 + offset, 326), radius=34, fill=(34, 42, 56, 220), outline=color, width=5)
        a.polygon([(130 + offset, 164), (44 + offset, 298), (88 + offset, 334), (154 + offset, 222)], fill=(32, 38, 52, 190), outline=color)
        a.polygon([(322 + offset, 164), (408 + offset, 298), (364 + offset, 334), (298 + offset, 222)], fill=(32, 38, 52, 190), outline=color)
        a.polygon([(162 + offset, 326), (226 + offset, 326), (202 + offset, 512), (124 + offset, 512)], fill=(30, 36, 49, 190), outline=color)
        a.polygon([(226 + offset, 326), (290 + offset, 326), (330 + offset, 512), (250 + offset, 512)], fill=(30, 36, 49, 190), outline=color)
    a.line((226, 36, 226, 512), fill=gold, width=5)
    a.text((160, 222), "TX", fill=cream, font=font(34))
    a.text((220, 258), "2X", fill=gold, font=font(42))
    avatar = avatar.resize((350, 420), Image.Resampling.LANCZOS)
    canvas.paste(avatar, (850, 320), avatar)

    diff_thumb = diffuse.resize((190, 190))
    glow_thumb = glow.resize((190, 190))
    canvas.paste(diff_thumb, (70, 500))
    canvas.paste(glow_thumb, (284, 500))
    d.rectangle((70, 500, 260, 690), outline=cream, width=2)
    d.rectangle((284, 500, 474, 690), outline=cream, width=2)
    d.text((70, 704), "diffuse", fill=cream, font=font(23))
    d.text((284, 704), "glow", fill=cream, font=font(23))
    return canvas


def write_metadata() -> None:
    (OUT / "rustchain_double_spend.skin").write_text(
        "\n".join(
            [
                "default,models/player/skins/rustchain_double_spend/rustchain_double_spend_diffuse.tga",
                "glow,models/player/skins/rustchain_double_spend/rustchain_double_spend_glow.tga",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (OUT / "README.md").write_text(
        """# RustChain Double Spend player skin

One original blockchain-themed player skin texture set for the RustChain Arena.

| File | Purpose |
|---|---|
| `rustchain_double_spend_diffuse.tga` | 1024x1024 diffuse map with split duplicate armor, conflicting transaction packets, and fork-race glyphs |
| `rustchain_double_spend_glow.tga` | 1024x1024 glow/emission map for the twin silhouettes, disputed center line, packet trails, and glitch tears |
| `rustchain_double_spend_preview.png` | Preview render and texture thumbnails |
| `rustchain_double_spend.skin` | Minimal DarkPlaces skin mapping for the texture pair |

## Theme

The design implements **Double Spend** from the open skin wishlist: a
twin/glitch-duplicate character with one cool cyan spend, one hot red spend,
and a disputed gold center line where both transactions race for the same
input.

## Integration notes

The texture files live under
`models/player/skins/rustchain_double_spend/` so they can be packed into the
RustChain PK3 with the rest of `pk3_build`.

The `.skin` file uses generic `default` and `glow` material names because this
repository does not currently include a canonical default player-model skin
template. If the final player model exposes specific material names, update
`rustchain_double_spend.skin` to map those material names to the same TGA
files.

## Regeneration

From the repository root:

```bash
python3 tools/generate_rustchain_double_spend_skin.py
```

The generator is deterministic and uses Pillow only for raster drawing and file
encoding.

## License

The generated textures, preview, and procedural source are licensed under
CC-BY-SA-4.0. See `LICENSE`.
""",
        encoding="utf-8",
    )
    (OUT / "LICENSE").write_text(
        """Creative Commons Attribution-ShareAlike 4.0 International

The generated RustChain Double Spend skin textures, preview image, and
procedural source are licensed under CC-BY-SA-4.0.

You are free to:

- Share: copy and redistribute the material in any medium or format.
- Adapt: remix, transform, and build upon the material for any purpose.

Under the following terms:

- Attribution: give appropriate credit to the contributor and this repository.
- ShareAlike: distribute adaptations under the same license.

Full license text:
https://creativecommons.org/licenses/by-sa/4.0/legalcode
""",
        encoding="utf-8",
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    diffuse, glow = make_diffuse_and_glow()
    preview = make_preview(diffuse, glow)

    diffuse.save(OUT / "rustchain_double_spend_diffuse.tga")
    glow.save(OUT / "rustchain_double_spend_glow.tga")
    preview.save(OUT / "rustchain_double_spend_preview.png")
    write_metadata()


if __name__ == "__main__":
    main()
