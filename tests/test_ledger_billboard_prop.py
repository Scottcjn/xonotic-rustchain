import importlib.util
from pathlib import Path
import struct
import unittest


ROOT = Path(__file__).resolve().parents[1]
PROP_DIR = ROOT / "pk3_build" / "models" / "props" / "rustchain_ledger_billboard"
MODULE_PATH = ROOT / "tools" / "generate_rustchain_ledger_billboard_prop.py"

try:
    from PIL import Image
except ImportError:
    Image = None


class LedgerBillboardPropPackageTests(unittest.TestCase):
    def test_metadata_files_are_packaged(self):
        readme = (PROP_DIR / "README.md").read_text()
        self.assertIn("Ledger Billboard", readme)
        self.assertIn("bounty #14015", readme)
        self.assertIn("CC-BY-SA-4.0", (PROP_DIR / "LICENSE").read_text())
        skin = (PROP_DIR / "rustchain_ledger_billboard.skin").read_text().splitlines()
        self.assertEqual(
            skin,
            [
                "frame,models/props/rustchain_ledger_billboard/textures/ledger_billboard_frame.tga",
                "screen,models/props/rustchain_ledger_billboard/textures/ledger_billboard_panel.tga",
                "glow,models/props/rustchain_ledger_billboard/textures/ledger_billboard_glow.tga",
            ],
        )

    def test_generator_constants_match_packaged_prop(self):
        spec = importlib.util.spec_from_file_location("ledger_billboard_generator", MODULE_PATH)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        try:
            spec.loader.exec_module(module)
        except ImportError as exc:
            self.skipTest(f"generator dependency unavailable: {exc}")
        self.assertEqual(module.OUT, PROP_DIR)
        self.assertEqual(module.TEX_SIZE, 256)
        self.assertIn("screen", module.MATERIALS)

    def test_iqm_header_has_static_prop_geometry(self):
        iqm_path = PROP_DIR / "rustchain_ledger_billboard.iqm"
        data = iqm_path.read_bytes()
        self.assertEqual(data[:16], b"INTERQUAKEMODEL\0")
        fields = struct.unpack("<27I", data[16:124])
        header = {
            "version": fields[0],
            "filesize": fields[1],
            "num_text": fields[3],
            "ofs_text": fields[4],
            "num_meshes": fields[5],
            "num_vertexarrays": fields[7],
            "num_vertexes": fields[8],
            "num_triangles": fields[10],
            "ofs_triangles": fields[11],
        }
        self.assertEqual(header["version"], 2)
        self.assertEqual(header["filesize"], len(data))
        self.assertEqual(header["num_meshes"], 3)
        self.assertEqual(header["num_vertexarrays"], 4)
        self.assertGreaterEqual(header["num_vertexes"], 300)
        self.assertGreaterEqual(header["num_triangles"], 180)
        text = data[header["ofs_text"] : header["ofs_text"] + header["num_text"]]
        self.assertIn(b"frame", text)
        self.assertIn(b"screen", text)
        self.assertIn(b"glow", text)

    @unittest.skipUnless(Image, "Pillow not available for image inspection")
    def test_packaged_images_have_expected_format_and_content(self):
        images = {
            "ledger_billboard_frame.tga": (256, 256),
            "ledger_billboard_panel.tga": (256, 256),
            "ledger_billboard_glow.tga": (256, 256),
            "preview.png": (960, 640),
        }
        for name, size in images.items():
            path = (PROP_DIR / name).resolve() if name == "preview.png" else (PROP_DIR / "textures" / name).resolve()
            self.assertTrue(path.is_file(), path)
            with Image.open(path) as image:
                self.assertEqual(image.size, size)

        with Image.open(PROP_DIR / "textures" / "ledger_billboard_panel.tga") as panel:
            colors = panel.convert("RGB").getcolors(maxcolors=1000000)
            assert colors is not None
            self.assertGreater(len(colors), 200)

        with Image.open(PROP_DIR / "textures" / "ledger_billboard_glow.tga") as glow:
            extrema = glow.getextrema()
            self.assertGreater(max(channel[1] for channel in extrema), 220)


if __name__ == "__main__":
    unittest.main()
