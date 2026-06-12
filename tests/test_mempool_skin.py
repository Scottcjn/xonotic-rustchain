import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKINS_DIR = ROOT / "pk3_build" / "models" / "player" / "skins"
MEMPOOL_DIR = SKINS_DIR / "rustchain_mempool"
MODULE_PATH = ROOT / "tools" / "generate_rustchain_mempool_skin.py"

try:
    from PIL import Image
except ImportError:
    Image = None


class MempoolSkinPackageTests(unittest.TestCase):
    def test_metadata_files_are_packaged(self):
        readme = (MEMPOOL_DIR / "README.md").read_text()
        self.assertIn("Mempool", readme)
        self.assertIn("CC-BY-SA-4.0", (MEMPOOL_DIR / "LICENSE").read_text())
        skin = (MEMPOOL_DIR / "rustchain_mempool.skin").read_text().splitlines()
        self.assertEqual(
            skin,
            [
                "default,models/player/skins/rustchain_mempool/rustchain_mempool_diffuse.tga",
                "glow,models/player/skins/rustchain_mempool/rustchain_mempool_glow.tga",
            ],
        )

    def test_generator_constants_match_packaged_skin(self):
        spec = importlib.util.spec_from_file_location("rustchain_mempool_generator", MODULE_PATH)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        try:
            spec.loader.exec_module(module)
        except ImportError as exc:
            self.skipTest(f"generator dependency unavailable: {exc}")
        self.assertEqual(module.SIZE, 1024)
        self.assertEqual(module.OUT, MEMPOOL_DIR)

    @unittest.skipUnless(Image, "Pillow not available for image inspection")
    def test_packaged_images_have_expected_format_and_content(self):
        diffuse_path = MEMPOOL_DIR / "rustchain_mempool_diffuse.tga"
        glow_path = MEMPOOL_DIR / "rustchain_mempool_glow.tga"
        preview_path = MEMPOOL_DIR / "rustchain_mempool_preview.png"

        for path, size in (
            (diffuse_path, (1024, 1024)),
            (glow_path, (1024, 1024)),
            (preview_path, (1400, 760)),
        ):
            self.assertTrue(path.is_file(), path)
            with Image.open(path) as image:
                self.assertEqual(image.size, size)

        with Image.open(diffuse_path) as diffuse:
            chest_queue = diffuse.crop((360, 400, 660, 610))
            upper_left_swarm = diffuse.crop((40, 120, 330, 360))
            self.assertNotEqual(
                chest_queue.resize((1, 1)).getpixel((0, 0)),
                upper_left_swarm.resize((1, 1)).getpixel((0, 0)),
            )

        with Image.open(glow_path) as glow:
            extrema = glow.getextrema()
            self.assertGreater(max(channel[1] for channel in extrema), 150)


if __name__ == "__main__":
    unittest.main()
