from __future__ import annotations

import base64


def _decode_regions(encoded: list[str] | tuple[str, ...]) -> list[bytes]:
    out = [base64.b64decode(x, validate=True) for x in encoded]
    if len(out) != 4 or any(len(x) != 32 for x in out):
        raise ValueError("region_shape")
    return out


def region_scores(before_b64, after_b64) -> list[int]:
    before = _decode_regions(before_b64)
    after = _decode_regions(after_b64)
    scores = []
    for b, a in zip(before, after):
        scores.append(sum(abs(x - y) for x, y in zip(b, a)))
    return scores


def top1_hard(before_b64, after_b64) -> dict:
    scores = region_scores(before_b64, after_b64)
    max_score = max(scores)
    selected = min(i for i, score in enumerate(scores) if score == max_score)
    return {
        "selected_regions": [selected],
        "exclusive": True,
        "scores": scores,
        "grants_input_authority": False,
    }


def exact_max_set(before_b64, after_b64) -> dict:
    scores = region_scores(before_b64, after_b64)
    max_score = max(scores)
    selected = [i for i, score in enumerate(scores) if score == max_score]
    return {
        "selected_regions": selected,
        "exclusive": len(selected) == 1,
        "scores": scores,
        "grants_input_authority": False,
    }
