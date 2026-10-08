import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
try:
    from candidate import LexicalNoveltyModel
except ModuleNotFoundError:
    LexicalNoveltyModel = None


class HeldoutCorpusTests(unittest.TestCase):
    def test_candidate_is_available(self):
        self.assertIsNotNone(LexicalNoveltyModel, "candidate not implemented")

    def test_training_and_evaluation_texts_are_not_exact_duplicates(self):
        corpus_path = HERE / "corpus.json"
        self.assertTrue(corpus_path.exists(), "frozen T2 corpus not created")
        corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
        train = {text.casefold().strip() for text in corpus["training_supported_only"]}
        evaluation = {case["task_summary"].casefold().strip() for case in corpus["evaluation"]}
        self.assertEqual(train & evaluation, set())
        self.assertGreaterEqual(len(train), 8)
        self.assertGreaterEqual(len(evaluation), 12)

    def test_only_supported_training_text_contributes_vocabulary(self):
        model = LexicalNoveltyModel.fit(["save selected draft"], threshold=0.2)
        self.assertEqual(model.vocabulary, frozenset({"save", "draft"}))

    def test_unseen_lexeme_changes_score_but_never_creates_authority(self):
        model = LexicalNoveltyModel.fit(["save draft"], threshold=0.2)
        self.assertGreater(model.score("archive draft"), 0)
        self.assertEqual(model.classify("archive draft"), "UNKNOWN_CHECK_REQUIRED")

    def test_empty_and_invalid_threshold_fail_closed(self):
        model = LexicalNoveltyModel.fit(["save draft"], threshold=0.2)
        self.assertEqual(model.classify(""), "UNKNOWN_CHECK_REQUIRED")
        with self.assertRaises(ValueError):
            LexicalNoveltyModel.fit(["save draft"], threshold=1.0)


if __name__ == "__main__":
    unittest.main()
