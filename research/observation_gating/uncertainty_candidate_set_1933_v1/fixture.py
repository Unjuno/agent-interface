from __future__ import annotations

import base64
from dataclasses import dataclass

REGION_COUNT = 4
REGION_BYTES = 32

@dataclass(frozen=True)
class Case:
    case_id: str
    family: str
    variant: int
    true_region: int
    regions_before_b64: tuple[str, ...]
    regions_after_b64: tuple[str, ...]


def _bytes_with_score(score: int, offset: int) -> bytes:
    if not 0 <= score <= REGION_BYTES:
        raise ValueError("score")
    out = bytearray(REGION_BYTES)
    for j in range(score):
        out[(offset + j) % REGION_BYTES] = 1
    return bytes(out)


def _pack(scores: list[int], case_index: int) -> tuple[tuple[str, ...], tuple[str, ...]]:
    before = []
    after = []
    for rid, score in enumerate(scores):
        b = bytes(REGION_BYTES)
        a = _bytes_with_score(score, (case_index * 7 + rid * 5) % REGION_BYTES)
        before.append(base64.b64encode(b).decode("ascii"))
        after.append(base64.b64encode(a).decode("ascii"))
    return tuple(before), tuple(after)


def generate_cases() -> list[Case]:
    cases: list[Case] = []
    idx = 0

    # 12 unique-max controls: 4 true regions x 3 variants.
    for true_region in range(REGION_COUNT):
        for variant in range(3):
            scores = [4 + ((rid + variant) % 3) for rid in range(REGION_COUNT)]
            scores[true_region] = 24 + variant
            before, after = _pack(scores, idx)
            cases.append(Case(
                case_id=f"unique-t{true_region}-v{variant}",
                family="UNIQUE_TRUE",
                variant=variant,
                true_region=true_region,
                regions_before_b64=before,
                regions_after_b64=after,
            ))
            idx += 1

    # 24 two-way ties: every ordered true/distractor pair x 2 variants.
    for true_region in range(REGION_COUNT):
        for distractor in range(REGION_COUNT):
            if distractor == true_region:
                continue
            for variant in range(2):
                scores = [5 + ((rid + variant) % 3) for rid in range(REGION_COUNT)]
                scores[true_region] = 20 + variant
                scores[distractor] = 20 + variant
                before, after = _pack(scores, idx)
                cases.append(Case(
                    case_id=f"tie2-t{true_region}-d{distractor}-v{variant}",
                    family="TWO_WAY_TIE",
                    variant=variant,
                    true_region=true_region,
                    regions_before_b64=before,
                    regions_after_b64=after,
                ))
                idx += 1

    # 12 three-way ties: one fixed omitted distractor per true region, 3 variants.
    for true_region in range(REGION_COUNT):
        omitted = (true_region + 1) % REGION_COUNT
        for variant in range(3):
            scores = [18 + variant] * REGION_COUNT
            scores[omitted] = 5 + variant
            before, after = _pack(scores, idx)
            cases.append(Case(
                case_id=f"tie3-t{true_region}-o{omitted}-v{variant}",
                family="THREE_WAY_TIE",
                variant=variant,
                true_region=true_region,
                regions_before_b64=before,
                regions_after_b64=after,
            ))
            idx += 1

    if len(cases) != 48:
        raise AssertionError(len(cases))
    return cases
