import struct
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROP_NAME = "rustchain_gpu_farm"
PROP = ROOT / "pk3_build" / "models" / "props" / PROP_NAME


class GpuFarmPropTest(unittest.TestCase):
    def test_required_bounty_files_exist(self):
        required = [
            f"{PROP_NAME}.iqm",
            f"{PROP_NAME}_0.skin",
            f"{PROP_NAME}_preview.png",
            f"{PROP_NAME}_source.obj",
            f"{PROP_NAME}_source.mtl",
            "README.md",
            "LICENSE",
            "gpu_farm_frame.tga",
            "gpu_farm_boards.tga",
            "gpu_farm_fans.tga",
            "gpu_farm_cables.tga",
        ]
        for name in required:
            self.assertTrue((PROP / name).is_file(), name)

    def test_iqm_header_describes_static_multimaterial_model(self):
        data = (PROP / f"{PROP_NAME}.iqm").read_bytes()
        values = struct.unpack("<16s27I", data[:124])
        self.assertEqual(values[0], b"INTERQUAKEMODEL\0")
        self.assertEqual(values[1], 2)
        self.assertEqual(values[2], len(data))
        self.assertEqual(values[6], 4)
        self.assertEqual(values[8], 3)
        self.assertGreater(values[9], 1000)
        self.assertGreater(values[11], 300)
        self.assertEqual(values[14], 0)
        self.assertEqual(values[18], 0)

    def test_textures_are_power_of_two_and_preview_is_png(self):
        for texture in PROP.glob("*.tga"):
            header = texture.read_bytes()[:18]
            self.assertEqual(header[2], 2, texture.name)
            self.assertEqual(int.from_bytes(header[12:14], "little"), 256, texture.name)
            self.assertEqual(int.from_bytes(header[14:16], "little"), 256, texture.name)
            self.assertEqual(header[16], 24, texture.name)
        self.assertEqual((PROP / f"{PROP_NAME}_preview.png").read_bytes()[:8], b"\x89PNG\r\n\x1a\n")

    def test_skin_maps_all_model_materials(self):
        skin = (PROP / f"{PROP_NAME}_0.skin").read_text(encoding="ascii")
        for material in ("rig_frame", "gpu_board", "fan_glow", "rtc_cable"):
            self.assertIn(material, skin)
        self.assertNotIn(".tga", skin)

    def test_readme_identifies_distinct_wishlist_item(self):
        readme = (PROP / "README.md").read_text(encoding="utf-8")
        self.assertIn("mining rig / gpu farm", readme.lower())
        self.assertIn("bounty #14015", readme.lower())


if __name__ == "__main__":
    unittest.main()
