import importlib.util
import math
import tempfile
import unittest
import wave
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "audio" / "generate_rustchain_objective_cues.py"
OBJECTIVE_DIR = ROOT / "pk3_build" / "sound" / "objectives" / "rustchain"
SPEC = importlib.util.spec_from_file_location("rustchain_objective_generator", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class ObjectiveCuePackageTests(unittest.TestCase):
    def test_required_objective_cues_are_present(self):
        self.assertEqual(
            set(MODULE.OBJECTIVE_CUES),
            {
                "capture_initiated",
                "node_contested",
                "validator_lock",
                "reward_route_open",
                "objective_lost",
            },
        )

    def test_generated_samples_are_finite_audible_and_short(self):
        for name, generator in MODULE.OBJECTIVE_CUES.items():
            samples = generator()
            self.assertGreater(len(samples), MODULE.SAMPLE_RATE // 2, name)
            self.assertLess(len(samples), MODULE.SAMPLE_RATE * 2, name)
            self.assertTrue(all(math.isfinite(sample) for sample in samples), name)
            self.assertGreater(max(abs(sample) for sample in samples), 0.05, name)

    def test_wav_output_is_mono_48khz_pcm(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "objective.wav"
            MODULE.write_wav(output, MODULE.validator_lock())
            with wave.open(str(output), "rb") as audio:
                self.assertEqual(audio.getnchannels(), 1)
                self.assertEqual(audio.getframerate(), 48_000)
                self.assertEqual(audio.getsampwidth(), 2)
                self.assertGreater(audio.getnframes(), 0)

    def test_metadata_files_are_packaged(self):
        readme = (OBJECTIVE_DIR / "README.md").read_text()
        self.assertIn("objective control cue", readme)
        self.assertIn("CC0 1.0", (OBJECTIVE_DIR / "LICENSE").read_text())

    def test_packaged_files_are_ogg_vorbis(self):
        for name in MODULE.OBJECTIVE_CUES:
            payload = (OBJECTIVE_DIR / f"{name}.ogg").read_bytes()
            self.assertTrue(payload.startswith(b"OggS"), name)
            self.assertIn(b"\x01vorbis", payload[:256], name)
            self.assertGreater(len(payload), 1_000, name)


if __name__ == "__main__":
    unittest.main()
