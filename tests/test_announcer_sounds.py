import importlib.util
import math
import tempfile
import unittest
import wave
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "audio" / "generate_rustchain_announcer.py"
SOUND_DIR = ROOT / "pk3_build" / "sound" / "announcer" / "rustchain"
SPEC = importlib.util.spec_from_file_location("rustchain_announcer_generator", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class AnnouncerGeneratorTests(unittest.TestCase):
    def test_required_cues_are_present(self):
        self.assertEqual(
            set(MODULE.CUES),
            {
                "begin",
                "prepare",
                "go",
                "firstblood",
                "impressive",
                "excellent",
                "humiliation",
                "lead_taken",
                "lead_lost",
                "1",
                "2",
                "3",
                "4",
                "5",
            },
        )

    def test_generated_samples_are_finite_and_audible(self):
        for name, generator in MODULE.CUES.items():
            samples = generator()
            self.assertGreater(len(samples), MODULE.SAMPLE_RATE // 3, name)
            self.assertTrue(all(math.isfinite(sample) for sample in samples), name)
            self.assertGreater(max(abs(sample) for sample in samples), 0.05, name)

    def test_wav_output_is_mono_48khz_pcm(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "cue.wav"
            MODULE.write_wav(output, MODULE.begin())
            with wave.open(str(output), "rb") as audio:
                self.assertEqual(audio.getnchannels(), 1)
                self.assertEqual(audio.getframerate(), 48_000)
                self.assertEqual(audio.getsampwidth(), 2)
                self.assertGreater(audio.getnframes(), 0)

    def test_countdown_duration_increases_with_number(self):
        lengths = [len(MODULE.countdown_cue(number)) for number in range(1, 6)]
        self.assertEqual(lengths, sorted(lengths))
        self.assertEqual(len(set(lengths)), 5)

    def test_packaged_files_are_ogg_vorbis(self):
        for name in MODULE.CUES:
            path = SOUND_DIR / f"{name}.ogg"
            payload = path.read_bytes()
            self.assertTrue(payload.startswith(b"OggS"), name)
            self.assertIn(b"\x01vorbis", payload[:256], name)
            self.assertGreater(len(payload), 1_000, name)


if __name__ == "__main__":
    unittest.main()
