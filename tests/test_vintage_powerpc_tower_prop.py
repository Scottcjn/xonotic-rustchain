import struct
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
PROP_NAME = "rustchain_vintage_powerpc_tower"
PROP = ROOT / "pk3_build" / "models" / "props" / PROP_NAME


class VintagePowerPCTowerPropTest(unittest.TestCase):
    def test_required_bounty_files_exist(self):
        required = [
            f"{PROP_NAME}.iqm",
            f"{PROP_NAME}.obj",
            f"{PROP_NAME}.mtl",
            f"{PROP_NAME}.skin",
            "preview.png",
            "README.md",
            "LICENSE",
            "textures/powerpc_case.tga",
            "textures/powerpc_dark.tga",
            "textures/powerpc_glow.tga",
            "textures/powerpc_label.tga",
        ]
        for name in required:
            self.assertTrue((PROP / name).is_file(), name)

    def test_iqm_header_is_static_model(self):
        data = (PROP / f"{PROP_NAME}.iqm").read_bytes()
        values = struct.unpack("<16s27I", data[:124])
        self.assertEqual(values[0], b"INTERQUAKEMODEL\0")
        self.assertEqual(values[1], 2)
        self.assertEqual(values[2], len(data))
        self.assertGreaterEqual(values[6], 1)
        self.assertGreaterEqual(values[8], 2)
        self.assertGreater(values[9], 40)
        self.assertGreater(values[11], 20)
        self.assertEqual(values[14], 0)
        self.assertEqual(values[18], 0)

    def test_textures_and_preview_have_expected_sizes(self):
        for texture in (PROP / "textures").glob("*.tga"):
            with Image.open(texture) as image:
                self.assertEqual(image.size, (256, 256), texture.name)
        with Image.open(PROP / "preview.png") as preview:
            self.assertEqual(preview.size, (1280, 720))
            self.assertEqual(preview.format, "PNG")

    def test_skin_and_obj_reference_all_materials(self):
        skin = (PROP / f"{PROP_NAME}.skin").read_text(encoding="ascii")
        obj = (PROP / f"{PROP_NAME}.obj").read_text(encoding="ascii")
        for material in ("powerpc_case", "powerpc_dark", "powerpc_glow", "powerpc_label"):
            self.assertIn(material, skin)
            self.assertIn(f"usemtl {material}", obj)

    def test_readme_identifies_distinct_wishlist_item(self):
        readme = (PROP / "README.md").read_text(encoding="utf-8")
        self.assertIn("bounty #14015", readme.lower())
        self.assertIn("vintage powerpc", readme.lower())
        self.assertIn("retro tower", readme.lower())


if __name__ == "__main__":
    unittest.main()
