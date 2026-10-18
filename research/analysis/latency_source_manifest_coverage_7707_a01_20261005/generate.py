"""Build deterministic byte-exact source-manifest coverage cases."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAIN = "e561b25b700680df4e6ffd2b92faf1dde1682ef7"


def make_case(case_id, lines, *, declared=None, eol="\n", fault=None):
    source = (eol.join(lines) + eol).encode("utf-8")
    declared = list(range(len(lines))) if declared is None else declared
    spans = []
    offset = 0
    for i, line in enumerate(lines):
        raw = line.encode("utf-8")
        if i in declared:
            fields = line.split("|", 2)
            spans.append({"line_no": i, "start_byte": offset, "end_byte": offset + len(raw),
                          "id": fields[1] if len(fields) > 1 else "",
                          "classification": fields[0] if fields else "",
                          "source_line": line, "revision": "r1"})
        offset += len(raw) + len(eol.encode("utf-8"))
    if fault == "duplicate_span" and len(spans) > 1:
        spans[1]["start_byte"], spans[1]["end_byte"] = spans[0]["start_byte"], spans[0]["end_byte"]
    elif fault == "duplicate_id" and len(spans) > 1:
        spans[1]["id"] = spans[0]["id"]
    elif fault == "partial_span" and spans:
        spans[0]["start_byte"] += 1
    return {"case_id": case_id, "source_text": source.decode("utf-8"),
            "source_sha256": hashlib.sha256(source).hexdigest(), "source_revision": "r1",
            "contract_revision": "r1", "clauses": spans}


cases = [
    make_case("valid_sat", ["RELAXABLE|sx0|x=0"]),
    make_case("pair_conflict", ["RELAXABLE|px0|x=0", "RELAXABLE|px1|x=1"]),
    make_case("two_muses", ["RELAXABLE|ax0|x=0", "RELAXABLE|ax1|x=1",
                            "RELAXABLE|by0|y=0", "RELAXABLE|by1|y=1"]),
    make_case("omitted_source_clause", ["RELAXABLE|kept|x=0", "RELAXABLE|omitted|x=1"], declared=[0]),
    make_case("duplicate_span", ["RELAXABLE|da|x=0", "RELAXABLE|db|x=1"], fault="duplicate_span"),
    make_case("duplicate_id", ["RELAXABLE|same|x=0", "RELAXABLE|same|x=1"], fault="duplicate_id"),
    make_case("partial_span", ["RELAXABLE|partial|x=0"], fault="partial_span"),
    make_case("unicode_prefix", ["RELAXABLE|café|x=0"]),
    make_case("declared_unknown", ["UNPARSEABLE|unknown|maybe"]),
    make_case("crlf", ["RELAXABLE|crlf_x0|x=0", "RELAXABLE|crlf_x1|x=1"], eol="\r\n"),
]
fixture = {"schema": "source-manifest-coverage-a01-v1", "frozen_main": MAIN, "cases": cases}
(HERE / "INPUT.json").write_text(json.dumps(fixture, sort_keys=True, separators=(",", ":")) + "\n",
                                 encoding="utf-8")
print(json.dumps({"cases": len(cases), "frozen_main": MAIN}, sort_keys=True))
