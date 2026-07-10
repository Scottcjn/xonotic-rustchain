import importlib.util
import math
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "audio" / "generate_rustchain_reward_alerts.py"
SOUND_DIR = ROOT / "pk3_build" / "sound" / "rewards" / "rustchain"
SPEC = importlib.util.spec_from_file_location("rustchain_reward_alert_generator", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class RewardAlertGeneratorTests(unittest.TestCase):
    def test_required_reward_alerts_are_present(self):
        self.assertEqual(
            set(MODULE.CUES),
            {
                "block_confirmed_pulse",
                "reward_mint",
                "wallet_credit",
                "chain_reorg_warning",
                "mining_tick_burst",
                "style_multiplier_lock",
            },
        )

    def test_generated_samples_are_finite_and_audible(self):
        for name, generator in MODULE.CUES.items():
            samples = generator()
            self.assertGreater(len(samples), MODULE.SAMPLE_RATE // 2, name)
            self.assertTrue(all(math.isfinite(sample) for sample in samples), name)
            self.assertGreater(max(abs(sample) for sample in samples), 0.05, name)

    def test_packaged_files_are_ogg_vorbis(self):
        for name in MODULE.CUES:
            path = SOUND_DIR / f"{name}.ogg"
            payload = path.read_bytes()
            self.assertTrue(payload.startswith(b"OggS"), name)
            self.assertIn(b"\x01vorbis", payload[:256], name)
            self.assertGreater(len(payload), 1_000, name)

    def test_metadata_files_are_packaged(self):
        self.assertIn("CC0 1.0", (SOUND_DIR / "LICENSE").read_text())
        readme = (SOUND_DIR / "README.md").read_text()
        self.assertIn("blood economy reward alerts", readme)
        self.assertIn("OGG Vorbis", readme)


if __name__ == "__main__":
    unittest.main()
