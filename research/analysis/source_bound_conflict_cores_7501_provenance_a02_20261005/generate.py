"""Generate source documents with byte-exact clause spans and pinned background."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAIN = "18bf390d0c230b5a2ee9675cebffbc0e51bfea2d2"
BACKGROUND_TEXT = "HARD|BG_DOMAIN_XY|x,y in {0,1}"
BACKGROUND = {"id": "BG_DOMAIN_XY", "revision": "bg-r1", "text": BACKGROUND_TEXT,
              "sha256": hashlib.sha256(BACKGROUND_TEXT.encode()).hexdigest(), "locked": True}


def make_case(case_id, lines, *, doc_rev="doc-r1", contract_rev="doc-r1",
              background=True, fault=None):
    source_text = "\n".join(lines) + "\n"
    source_bytes = source_text.encode("utf-8")
    clauses = []
    offset = 0
    for line in lines:
        raw = line.encode("utf-8")
        parts = line.split("|", 2)
        classification = parts[0] if parts else ""
        source_id = parts[1] if len(parts) > 1 else ""
        clauses.append({"id": source_id, "classification": classification,
                        "source_line": line, "start_byte": offset,
                        "end_byte": offset + len(raw), "revision": doc_rev})
        offset += len(raw) + 1
    if fault == "shift_span" and clauses:
        clauses[0]["start_byte"] += 1
    if fault == "duplicate_span" and len(clauses) > 1:
        clauses[1]["start_byte"] = clauses[0]["start_byte"]
        clauses[1]["end_byte"] = clauses[0]["end_byte"]
    digest = hashlib.sha256(source_bytes).hexdigest()
    if fault == "source_digest":
        digest = "0" * 64
    return {"case_id": case_id, "source_text": source_text,
            "source_sha256": digest, "source_revision": doc_rev,
            "contract_revision": contract_rev, "clauses": clauses,
            "hard_background": dict(BACKGROUND) if background else None,
            "frozen_main": MAIN}


cases = [
    make_case("valid_sat", ["RELAXABLE|sat_x0|x=0"]),
    make_case("pair_conflict", ["RELAXABLE|pair_x0|x=0", "RELAXABLE|pair_x1|x=1"]),
    make_case("two_muses", ["RELAXABLE|mx0|x=0", "RELAXABLE|mx1|x=1",
                            "RELAXABLE|my0|y=0", "RELAXABLE|my1|y=1"]),
    make_case("bad_source_digest", ["RELAXABLE|bad_hash|x=0"], fault="source_digest"),
    make_case("shifted_span", ["RELAXABLE|bad_span|x=0"], fault="shift_span"),
    make_case("duplicate_span", ["RELAXABLE|dup_a|x=0", "RELAXABLE|dup_b|x=1"],
              fault="duplicate_span"),
    make_case("stale_revision", ["RELAXABLE|stale_x0|x=0"], contract_rev="doc-r0"),
    make_case("missing_background", ["RELAXABLE|no_bg_x0|x=0"], background=False),
    make_case("hard_background_conflict", ["RELAXABLE|outside_domain|x=2"]),
    make_case("unknown_clause", ["UNPARSEABLE|unknown_x|maybe x=0"]),
]
fixture = {"schema": "source-bound-mus-a02-v1", "frozen_main": MAIN,
           "hard_background_pin": BACKGROUND["sha256"], "cases": cases}
(HERE / "INPUT.json").write_text(json.dumps(fixture, sort_keys=True, separators=(",", ":")) + "\n")
print(json.dumps({"cases": len(cases), "valid_sat": 1, "pair_conflict": 1,
                  "two_independent_muses": 1, "provenance_rejections": 3,
                  "stale_revision": 1, "missing_background": 1,
                  "hard_background_conflict": 1, "unknown": 1}, sort_keys=True))
