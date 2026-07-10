import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "audio" / "generate_rustchain_antiquity_cues.py"
CUE_DIR = ROOT / "pk3_build" / "sound" / "antiquity" / "rustchain"

try:
    import soundfile as sf
except ImportError:
    sf = None

SPEC = importlib.util.spec_from_file_location("rustchain_antiquity_cues", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class AntiquityCueSoundPackageTests(unittest.TestCase):
    def test_required_cues_are_present(self):
        self.assertEqual(
            set(MODULE.CUES),
            {
                "crt_boot_nonce",
                "power8_validator_spin",
                "g4_cube_sync",
                "antiquity_weight_boost",
                "vm_rejected_flatline",
            },
        )

    def test_generated_samples_are_finite_audible_and_short(self):
        for name, generator in MODULE.CUES.items():
            samples = generator()
            self.assertGreater(len(samples), MODULE.SAMPLE_RATE // 2, name)
            self.assertLess(len(samples), MODULE.SAMPLE_RATE * 2, name)
            self.assertTrue((abs(samples) < 10).all(), name)
            self.assertGreater(float(abs(samples).max()), 0.05, name)

    def test_metadata_files_are_packaged(self):
        readme = (CUE_DIR / "README.md").read_text()
        self.assertIn("Proof-of-Antiquity hardware cues", readme)
        self.assertIn("bounty #293", readme)
        self.assertIn("CC0 1.0", (CUE_DIR / "LICENSE").read_text())

    def test_packaged_files_are_ogg_vorbis(self):
        for name in MODULE.CUES:
            path = CUE_DIR / f"{name}.ogg"
            payload = path.read_bytes()
            self.assertTrue(payload.startswith(b"OggS"), name)
            self.assertIn(b"\x01vorbis", payload[:256], name)
            self.assertGreater(len(payload), 1_000, name)

    @unittest.skipUnless(sf, "soundfile not available for OGG metadata inspection")
    def test_packaged_audio_is_mono_48khz_and_not_silent(self):
        for name in MODULE.CUES:
            path = CUE_DIR / f"{name}.ogg"
            info = sf.info(path)
            self.assertEqual(info.samplerate, MODULE.SAMPLE_RATE, name)
            self.assertEqual(info.channels, 1, name)
            self.assertGreater(info.duration, 0.5, name)
            self.assertLess(info.duration, 2.0, name)
            samples, sample_rate = sf.read(path, dtype="float32")
            self.assertEqual(sample_rate, MODULE.SAMPLE_RATE, name)
            self.assertLessEqual(float(abs(samples).max()), 0.86, name)
            self.assertGreater(float((samples * samples).mean() ** 0.5), 0.015, name)


if __name__ == "__main__":
    unittest.main()
