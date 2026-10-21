"""Post-run reproduction test that never writes into the frozen input package."""
import hashlib
import tempfile
from pathlib import Path

import test_visual_context_staleness as frozen_v1

ROOT = frozen_v1.ROOT


class VisualContextStalenessImmutablePromptTests(
        frozen_v1.VisualContextStalenessTests):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._runtime_dir = tempfile.TemporaryDirectory(
            prefix="visual-context-staleness-runtime-"
        )
        runtime_root = Path(cls._runtime_dir.name)
        begin_model_turn = cls.f["begin_model_turn"]

        def begin_with_temporary_prompt(planner, _root, image, effect_memory,
                                        source_health, source_ammo,
                                        prior_soft_event_summary, output_schema):
            return begin_model_turn(
                planner, runtime_root, image, effect_memory, source_health,
                source_ammo, prior_soft_event_summary, output_schema
            )

        cls.f["begin_model_turn"] = begin_with_temporary_prompt
        cls._runtime_root = runtime_root

    @classmethod
    def tearDownClass(cls):
        try:
            cls._runtime_dir.cleanup()
        finally:
            super().tearDownClass()

    def run_case(self, copy_hash):
        prompt_path = ROOT / "prompt.txt"
        prompt_before = hashlib.sha256(prompt_path.read_bytes()).hexdigest()
        result = super().run_case(copy_hash)
        self.assertTrue((self._runtime_root / "prompt.txt").is_file())
        self.assertEqual(
            hashlib.sha256(prompt_path.read_bytes()).hexdigest(), prompt_before
        )
        return result


if __name__ == "__main__":
    import unittest

    unittest.main(verbosity=2)
