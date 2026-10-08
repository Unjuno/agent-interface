"""Finite structured contract-preservation gate for Issue #6471; no ASR/model."""
import json
from pathlib import Path

ROOT = Path(__file__).parent
CRITICAL = ("speech_act", "effect", "target", "recipient", "bound", "forbidden")


def _span(text, phrase):
    if phrase is None:
        return None
    start = text.find(phrase)
    return None if start < 0 else [start, start + len(phrase)]


def evaluate(case):
    errors = []
    links = {}
    for slot, link in case["span_links"].items():
        src, hyp = link["source"], link["transcript"]
        source_span = _span(case["source_text"], src)
        transcript_span = _span(case["transcript"], hyp)
        if source_span is None:
            errors.append(f"SOURCE_SPAN_MISSING:{slot}")
        if hyp is not None and transcript_span is None:
            errors.append(f"TRANSCRIPT_SPAN_MISSING:{slot}")
        links[slot] = {"source": source_span, "transcript": transcript_span}

    source, observed = case["source_contract"], case["transcript_slots"]
    for slot in ("target", "recipient", "bound"):
        if slot not in case["span_links"]:
            if source.get(slot) is not None or observed.get(slot) is not None:
                errors.append(f"CRITICAL_SLOT_SPAN_ABSENT:{slot}")
            continue
        link = case["span_links"][slot]
        if link["source"] != source.get(slot) or link["transcript"] != observed.get(slot):
            errors.append(f"CRITICAL_SLOT_SPAN_LABEL_MISMATCH:{slot}")
    changed = [key for key in CRITICAL if source.get(key) != observed.get(key)]
    ambiguous = bool(observed.get("ambiguity"))
    if errors:
        decision = "STOP_INTEGRITY"
    elif ambiguous:
        decision = "CLARIFY"
    elif changed:
        decision = "BLOCK"
    else:
        decision = "ALLOW_TO_SEPARATE_AUTHORITY_GATE"
    return {"case_id": case["id"], "decision": decision, "changed_slots": changed,
            "span_links": links, "errors": sorted(errors)}


def main():
    cases = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))["cases"]
    rows = [evaluate(case) for case in cases]
    (ROOT / "candidate.raw.json").write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(rows, sort_keys=True))


if __name__ == "__main__":
    main()
