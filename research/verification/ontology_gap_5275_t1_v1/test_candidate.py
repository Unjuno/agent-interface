import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    import candidate
except ModuleNotFoundError:
    candidate = None


class LexicalConfidenceTests(unittest.TestCase):
    def test_candidate_module_exists(self):
        self.assertIsNotNone(candidate, "candidate module has not been implemented")

    def test_training_uses_only_supported_training_text(self):
        train = ["save the selected draft and verify saved state"]
        model = candidate.LexicalNoveltyModel.fit(train, threshold=0.2)
        self.assertEqual(model.vocabulary, frozenset({"save", "draft", "verify", "saved", "state"}))

    def test_known_paraphrase_stays_below_abstention_threshold(self):
        model = candidate.LexicalNoveltyModel.fit(
            ["save the selected draft and verify saved state"], threshold=0.2
        )
        self.assertEqual(model.classify("save selected draft and verify the saved state"), "PLAN_COVERED")

    def test_semantically_novel_words_raise_unknown_without_hardcoded_terms(self):
        model = candidate.LexicalNoveltyModel.fit(
            ["archive selected customer record and verify reversibility"], threshold=0.2
        )
        self.assertEqual(model.classify("archive selected customer record under legal hold"), "UNKNOWN_CHECK_REQUIRED")

    def test_threshold_is_strict_and_empty_text_abstains(self):
        model = candidate.LexicalNoveltyModel.fit(["save draft"], threshold=0.5)
        self.assertEqual(model.classify("save draft unknown"), "PLAN_COVERED")
        self.assertEqual(model.classify(""), "UNKNOWN_CHECK_REQUIRED")


if __name__ == "__main__":
    unittest.main()
