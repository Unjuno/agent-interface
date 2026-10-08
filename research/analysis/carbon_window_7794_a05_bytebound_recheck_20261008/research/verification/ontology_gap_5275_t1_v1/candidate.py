"""One-class lexical confidence probe; it does not issue action verdicts."""

from dataclasses import dataclass
import re

_STOP = frozenset({
    "a", "an", "and", "as", "before", "by", "for", "from", "in", "into",
    "is", "it", "of", "on", "or", "selected", "the", "then", "to", "under",
    "while", "with",
})
_WORD = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class LexicalNoveltyModel:
    vocabulary: frozenset[str]
    threshold: float

    @classmethod
    def fit(cls, supported_training_text, threshold):
        if not 0.0 <= threshold < 1.0:
            raise ValueError("threshold must be in [0, 1)")
        vocabulary = frozenset(
            token
            for text in supported_training_text
            for token in _WORD.findall(text.lower())
            if token not in _STOP
        )
        if not vocabulary:
            raise ValueError("training corpus must contain informative tokens")
        return cls(vocabulary=vocabulary, threshold=threshold)

    def score(self, task_summary):
        tokens = [token for token in _WORD.findall(task_summary.lower()) if token not in _STOP]
        if not tokens:
            return 1.0
        return sum(token not in self.vocabulary for token in tokens) / len(tokens)

    def classify(self, task_summary):
        return (
            "UNKNOWN_CHECK_REQUIRED"
            if self.score(task_summary) > self.threshold
            else "PLAN_COVERED"
        )
