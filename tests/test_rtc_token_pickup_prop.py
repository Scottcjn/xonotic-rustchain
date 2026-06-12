import struct
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
PROP_NAME = "rustchain_rtc_token_pickup"
PROP = ROOT / "pk3_build" / "models" / "props" / PROP_NAME


class RtcTokenPickupPropTest(unittest.TestCase):
    def test_required_bounty_files_exist(self):
        required = [
            f"{PROP_NAME}.iqm",
            f"{PROP_NAME}_0.skin",
            f"{PROP_NAME}_preview.png",
            f"{PROP_NAME}_source.obj",
            f"{PROP_NAME}_source.mtl",
            "README.md",
            "LICENSE",
            "rtc_token_pickup_gold.tga",
            "rtc_token_pickup_edge.tga",
            "rtc_token_pickup_glow.tga",
            "rtc_token_pickup_base.tga",
        ]
        for name in required:
            self.assertTrue((PROP / name).is_file(), name)

    def test_iqm_header_describes_static_multimaterial_model(self):
        data = (PROP / f"{PROP_NAME}.iqm").read_bytes()
        values = struct.unpack("<16s27I", data[:124])
        self.assertEqual(values[0], b"INTERQUAKEMODEL\0")
        self.assertEqual(values[1], 2)
        self.assertEqual(values[2], len(data))
        self.assertEqual(values[6], 4)  # one mesh per material
        self.assertEqual(values[8], 3)  # positions, texcoords, normals
        self.assertGreater(values[9], 500)
        self.assertGreater(values[11], 170)
        self.assertEqual(values[14], 0)  # no joints
        self.assertEqual(values[18], 0)  # no animations

    def test_textures_are_power_of_two_and_preview_is_png(self):
        for texture in PROP.glob("*.tga"):
            with Image.open(texture) as image:
                self.assertEqual(image.size, (256, 256), texture.name)
        with Image.open(PROP / f"{PROP_NAME}_preview.png") as preview:
            self.assertEqual(preview.size, (1280, 720))
            self.assertEqual(preview.format, "PNG")

    def test_skin_maps_all_model_materials(self):
        skin = (PROP / f"{PROP_NAME}_0.skin").read_text(encoding="ascii")
        for material in ("token_gold", "token_edge", "pickup_glow", "pickup_base"):
            self.assertIn(material, skin)
        self.assertNotIn(".tga", skin)

    def test_readme_identifies_distinct_wishlist_item(self):
        readme = (PROP / "README.md").read_text(encoding="utf-8")
        self.assertIn("RTC token pickup", readme)
        self.assertIn("bounty #14015", readme.lower())


if __name__ == "__main__":
    unittest.main()
