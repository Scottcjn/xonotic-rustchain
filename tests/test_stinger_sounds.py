import importlib.util
import math
import tempfile
import unittest
import wave
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "audio" / "generate_rustchain_stingers.py"
STINGER_DIR = ROOT / "pk3_build" / "sound" / "stingers" / "rustchain"
SPEC = importlib.util.spec_from_file_location("rustchain_stinger_generator", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class StingerSoundPackageTests(unittest.TestCase):
    def test_required_stingers_are_present(self):
        self.assertEqual(
            set(MODULE.STINGERS),
            {
                "double_spend",
                "triple_fork",
                "consensus_reached",
                "block_confirmed",
                "attack_detected",
            },
        )

    def test_generated_samples_are_finite_audible_and_short(self):
        for name, generator in MODULE.STINGERS.items():
            samples = generator()
            self.assertGreater(len(samples), MODULE.SAMPLE_RATE // 2, name)
            self.assertLess(len(samples), MODULE.SAMPLE_RATE * 2, name)
            self.assertTrue(all(math.isfinite(sample) for sample in samples), name)
            self.assertGreater(max(abs(sample) for sample in samples), 0.05, name)

    def test_wav_output_is_mono_48khz_pcm(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "stinger.wav"
            MODULE.write_wav(output, MODULE.consensus_reached())
            with wave.open(str(output), "rb") as audio:
                self.assertEqual(audio.getnchannels(), 1)
                self.assertEqual(audio.getframerate(), 48_000)
                self.assertEqual(audio.getsampwidth(), 2)
                self.assertGreater(audio.getnframes(), 0)

    def test_metadata_files_are_packaged(self):
        readme = (STINGER_DIR / "README.md").read_text()
        self.assertIn("kill-streak stinger", readme)
        self.assertIn("CC0 1.0", (STINGER_DIR / "LICENSE").read_text())

    def test_packaged_files_are_ogg_vorbis(self):
        for name in MODULE.STINGERS:
            path = STINGER_DIR / f"{name}.ogg"
            payload = path.read_bytes()
            self.assertTrue(payload.startswith(b"OggS"), name)
            self.assertIn(b"\x01vorbis", payload[:256], name)
            self.assertGreater(len(payload), 1_000, name)


if __name__ == "__main__":
    unittest.main()
