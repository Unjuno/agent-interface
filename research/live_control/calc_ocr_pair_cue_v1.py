"""Compare two OCR TSVs with explicit expected decimal strings.

This is a visual cue only: it neither proves a saved workbook effect nor grants
input authority. The caller owns capture freshness, geometry and resource bounds.
"""
import csv
import io
import math
import re


def _word(tsv):
    try:
        reader = csv.DictReader(io.StringIO(tsv), delimiter="\t")
        if reader.fieldnames is None or not {"level", "conf", "text"}.issubset(reader.fieldnames):
            return None
        words = []
        for row in reader:
            text = (row.get("text") or "").strip()
            if not text:
                continue
            confidence = float(row["conf"])
            if (row.get("level") != "5" or not math.isfinite(confidence)
                    or not 90 <= confidence <= 100 or re.fullmatch(r"[0-9]+", text) is None):
                return None
            words.append(text)
        return words[0] if len(words) == 1 else None
    except (ValueError, TypeError, KeyError, csv.Error):
        return None


def classify_pair(first_tsv, second_tsv, *, expected):
    """Return filled, wrong, or unknown; reject malformed expected values."""
    if (type(expected) is not tuple or len(expected) != 2
            or any(type(value) is not str or re.fullmatch(r"[0-9]+", value) is None
                   for value in expected)):
        raise ValueError("expected must contain two nonempty ASCII decimal strings")
    first, second = _word(first_tsv), _word(second_tsv)
    if first is None or second is None:
        return "unknown"
    return "filled" if (first, second) == expected else "wrong"
