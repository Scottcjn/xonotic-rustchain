import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MUSIC_DIR = ROOT / "pk3_build" / "sound" / "music" / "rustchain"
TRACK_PATH = MUSIC_DIR / "chain_reactor_loop.ogg"
MODULE_PATH = ROOT / "tools" / "audio" / "generate_rustchain_music.py"

try:
    import soundfile as sf
except ImportError:
    sf = None


class MusicLoopPackageTests(unittest.TestCase):
    def test_packaged_track_is_ogg_vorbis(self):
        payload = TRACK_PATH.read_bytes()
        self.assertTrue(payload.startswith(b"OggS"))
        self.assertIn(b"\x01vorbis", payload[:256])
        self.assertGreater(len(payload), 100_000)

    def test_metadata_files_are_packaged(self):
        self.assertIn("CC0 1.0", (MUSIC_DIR / "LICENSE").read_text())
        readme = (MUSIC_DIR / "README.md").read_text()
        self.assertIn("OGG Vorbis", readme)
        self.assertIn("3:12", readme)

    def test_generator_constants_match_packaged_track_claim(self):
        spec = importlib.util.spec_from_file_location("rustchain_music_generator", MODULE_PATH)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        try:
            spec.loader.exec_module(module)
        except ImportError as exc:
            self.skipTest(f"generator dependency unavailable: {exc}")
        self.assertEqual(module.SAMPLE_RATE, 48_000)
        self.assertEqual(module.BPM, 160)
        self.assertEqual(module.BARS, 128)
        self.assertAlmostEqual(module.DURATION_SECONDS, 192.0)

    @unittest.skipUnless(sf, "soundfile not available for OGG metadata inspection")
    def test_packaged_track_is_mono_48khz_and_click_safe(self):
        info = sf.info(TRACK_PATH)
        self.assertEqual(info.samplerate, 48_000)
        self.assertEqual(info.channels, 1)
        self.assertAlmostEqual(info.duration, 192.0, delta=0.1)
        samples, sample_rate = sf.read(TRACK_PATH, dtype="float32")
        self.assertEqual(sample_rate, 48_000)
        self.assertLessEqual(float(abs(samples).max()), 0.82)
        self.assertGreater(float((samples * samples).mean() ** 0.5), 0.025)
        self.assertLess(float(abs(samples[:32]).max()), 0.08)
        self.assertLess(float(abs(samples[-32:]).max()), 0.08)


if __name__ == "__main__":
    unittest.main()
