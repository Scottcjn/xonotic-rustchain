import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKINS_DIR = ROOT / "pk3_build" / "models" / "player" / "skins"
DOUBLE_SPEND_DIR = SKINS_DIR / "rustchain_double_spend"
MODULE_PATH = ROOT / "tools" / "generate_rustchain_double_spend_skin.py"

try:
    from PIL import Image
except ImportError:
    Image = None


class DoubleSpendSkinPackageTests(unittest.TestCase):
    def test_metadata_files_are_packaged(self):
        readme = (DOUBLE_SPEND_DIR / "README.md").read_text()
        self.assertIn("Double Spend", readme)
        self.assertIn("CC-BY-SA-4.0", (DOUBLE_SPEND_DIR / "LICENSE").read_text())
        skin = (DOUBLE_SPEND_DIR / "rustchain_double_spend.skin").read_text().splitlines()
        self.assertEqual(
            skin,
            [
                "default,models/player/skins/rustchain_double_spend/rustchain_double_spend_diffuse.tga",
                "glow,models/player/skins/rustchain_double_spend/rustchain_double_spend_glow.tga",
            ],
        )

    def test_generator_constants_match_packaged_skin(self):
        spec = importlib.util.spec_from_file_location("rustchain_double_spend_generator", MODULE_PATH)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        try:
            spec.loader.exec_module(module)
        except ImportError as exc:
            self.skipTest(f"generator dependency unavailable: {exc}")
        self.assertEqual(module.SIZE, 1024)
        self.assertEqual(module.OUT, DOUBLE_SPEND_DIR)

    @unittest.skipUnless(Image, "Pillow not available for image inspection")
    def test_packaged_images_have_expected_format_and_content(self):
        diffuse_path = DOUBLE_SPEND_DIR / "rustchain_double_spend_diffuse.tga"
        glow_path = DOUBLE_SPEND_DIR / "rustchain_double_spend_glow.tga"
        preview_path = DOUBLE_SPEND_DIR / "rustchain_double_spend_preview.png"

        for path, size in (
            (diffuse_path, (1024, 1024)),
            (glow_path, (1024, 1024)),
            (preview_path, (1400, 760)),
        ):
            self.assertTrue(path.is_file(), path)
            with Image.open(path) as image:
                self.assertEqual(image.size, size)

        with Image.open(diffuse_path) as diffuse:
            left = diffuse.crop((0, 0, 512, 1024)).resize((1, 1)).getpixel((0, 0))
            right = diffuse.crop((512, 0, 1024, 1024)).resize((1, 1)).getpixel((0, 0))
            center = diffuse.crop((438, 346, 586, 608)).resize((1, 1)).getpixel((0, 0))
            self.assertGreater(abs(left[0] - right[0]) + abs(left[2] - right[2]), 20)
            self.assertGreater(center[0] + center[1], left[0] + left[1])

        with Image.open(glow_path) as glow:
            extrema = glow.getextrema()
            self.assertGreater(max(channel[1] for channel in extrema), 150)


if __name__ == "__main__":
    unittest.main()
