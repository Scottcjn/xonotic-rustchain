import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKINS_DIR = ROOT / "pk3_build" / "models" / "player" / "skins"
GENESIS_DIR = SKINS_DIR / "rustchain_genesis_founder"
MODULE_PATH = ROOT / "tools" / "generate_rustchain_genesis_founder_skin.py"

try:
    from PIL import Image
except ImportError:
    Image = None


class GenesisFounderSkinPackageTests(unittest.TestCase):
    def test_metadata_files_are_packaged(self):
        readme = (GENESIS_DIR / "README.md").read_text()
        self.assertIn("Genesis / Founder", readme)
        self.assertIn("CC-BY-SA-4.0", (GENESIS_DIR / "LICENSE").read_text())
        skin = (GENESIS_DIR / "rustchain_genesis_founder.skin").read_text().splitlines()
        self.assertEqual(
            skin,
            [
                "default,models/player/skins/rustchain_genesis_founder/rustchain_genesis_founder_diffuse.tga",
                "glow,models/player/skins/rustchain_genesis_founder/rustchain_genesis_founder_glow.tga",
            ],
        )

    def test_generator_constants_match_packaged_skin(self):
        spec = importlib.util.spec_from_file_location("rustchain_genesis_founder_generator", MODULE_PATH)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        try:
            spec.loader.exec_module(module)
        except ImportError as exc:
            self.skipTest(f"generator dependency unavailable: {exc}")
        self.assertEqual(module.SIZE, 1024)
        self.assertEqual(module.OUT, GENESIS_DIR)

    @unittest.skipUnless(Image, "Pillow not available for image inspection")
    def test_packaged_images_have_expected_format_and_content(self):
        diffuse_path = GENESIS_DIR / "rustchain_genesis_founder_diffuse.tga"
        glow_path = GENESIS_DIR / "rustchain_genesis_founder_glow.tga"
        preview_path = GENESIS_DIR / "rustchain_genesis_founder_preview.png"

        for path, size in (
            (diffuse_path, (1024, 1024)),
            (glow_path, (1024, 1024)),
            (preview_path, (1400, 760)),
        ):
            self.assertTrue(path.is_file(), path)
            with Image.open(path) as image:
                self.assertEqual(image.size, size)

        with Image.open(diffuse_path) as diffuse:
            medallion = diffuse.crop((400, 410, 624, 586))
            leg_plate = diffuse.crop((300, 800, 720, 970))
            self.assertNotEqual(
                medallion.resize((1, 1)).getpixel((0, 0)),
                leg_plate.resize((1, 1)).getpixel((0, 0)),
            )

        with Image.open(glow_path) as glow:
            self.assertGreater(max(channel[1] for channel in glow.getextrema()), 130)


if __name__ == "__main__":
    unittest.main()
