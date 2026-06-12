import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKINS_DIR = ROOT / "pk3_build" / "models" / "player" / "skins"
HASHCANNON_DIR = SKINS_DIR / "rustchain_hashcannon"
MODULE_PATH = ROOT / "tools" / "generate_rustchain_hashcannon_skin.py"

try:
    from PIL import Image
except ImportError:
    Image = None


class HashCannonSkinPackageTests(unittest.TestCase):
    def test_metadata_files_are_packaged(self):
        readme = (HASHCANNON_DIR / "README.md").read_text()
        self.assertIn("HashCannon", readme)
        self.assertIn("CC-BY-SA-4.0", (HASHCANNON_DIR / "LICENSE").read_text())
        skin = (HASHCANNON_DIR / "rustchain_hashcannon.skin").read_text().splitlines()
        self.assertEqual(
            skin,
            [
                "default,models/player/skins/rustchain_hashcannon/rustchain_hashcannon_diffuse.tga",
                "glow,models/player/skins/rustchain_hashcannon/rustchain_hashcannon_glow.tga",
            ],
        )

    def test_generator_constants_match_packaged_skin(self):
        spec = importlib.util.spec_from_file_location("rustchain_hashcannon_generator", MODULE_PATH)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        try:
            spec.loader.exec_module(module)
        except ImportError as exc:
            self.skipTest(f"generator dependency unavailable: {exc}")
        self.assertEqual(module.SIZE, 1024)
        self.assertEqual(module.OUT, HASHCANNON_DIR)

    @unittest.skipUnless(Image, "Pillow not available for image inspection")
    def test_packaged_images_have_expected_format_and_content(self):
        diffuse_path = HASHCANNON_DIR / "rustchain_hashcannon_diffuse.tga"
        glow_path = HASHCANNON_DIR / "rustchain_hashcannon_glow.tga"
        preview_path = HASHCANNON_DIR / "rustchain_hashcannon_preview.png"

        for path, size in (
            (diffuse_path, (1024, 1024)),
            (glow_path, (1024, 1024)),
            (preview_path, (1400, 760)),
        ):
            self.assertTrue(path.is_file(), path)
            with Image.open(path) as image:
                self.assertEqual(image.size, size)

        with Image.open(diffuse_path) as diffuse:
            top_barrel = diffuse.crop((180, 520, 920, 700))
            lower_legs = diffuse.crop((260, 760, 760, 990))
            self.assertNotEqual(
                top_barrel.resize((1, 1)).getpixel((0, 0)),
                lower_legs.resize((1, 1)).getpixel((0, 0)),
            )

        with Image.open(glow_path) as glow:
            extrema = glow.getextrema()
            self.assertGreater(max(channel[1] for channel in extrema), 150)


if __name__ == "__main__":
    unittest.main()
