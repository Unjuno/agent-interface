"""Synthetic exact-target binding comparison for Issue #5993 T0."""
from __future__ import annotations

import hashlib
import json
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
CORPUS_PATH = HERE / "corpus.json"
CONFUSABLES_PATH = HERE / "confusables.txt"
DERIVED_PATH = HERE / "DerivedCoreProperties.txt"
EXPECTED_DATA = {
    "confusables.txt": "6ED3EE967C9DFDF6677D563C9985182FBC50A2EFB7D6059CD57B2E2CE18F5B92",
    "DerivedCoreProperties.txt": "09C928886A178FCAFD93C29E4BD59073A058E5A100B716D425CB563AB50F68C9",
}
OUTPUT_PATH = HERE / "candidate.jsonl"
POLICIES = ("string_only", "skeleton_warning_only", "exact_fresh_binding")


def verify_data_files() -> None:
    for path in (CONFUSABLES_PATH, DERIVED_PATH):
        actual = hashlib.sha256(path.read_bytes()).hexdigest().upper()
        if actual != EXPECTED_DATA[path.name]:
            raise ValueError(f"pinned source hash mismatch: {path.name}")


def parse_confusables(path: Path) -> dict[str, str]:
    table: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        body = raw.split("#", 1)[0].strip()
        if not body:
            continue
        fields = [part.strip() for part in body.split(";")]
        if len(fields) < 3:
            raise ValueError("malformed confusables row")
        source = fields[0].split()
        target = fields[1].split()
        if len(source) != 1 or not target:
            raise ValueError("unexpected mapping arity for frozen Unicode 18 data")
        char = chr(int(source[0], 16))
        mapped = "".join(chr(int(codepoint, 16)) for codepoint in target)
        if char in table:
            raise ValueError("duplicate confusable source")
        table[char] = mapped
    return table


def parse_default_ignorables(path: Path) -> set[int]:
    result: set[int] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        body = raw.split("#", 1)[0].strip()
        if not body:
            continue
        field, prop = (part.strip() for part in body.split(";", 1))
        if prop != "Default_Ignorable_Code_Point":
            continue
        if ".." in field:
            lo, hi = (int(part, 16) for part in field.split(".."))
        else:
            lo = hi = int(field, 16)
        result.update(range(lo, hi + 1))
    if not result:
        raise ValueError("Unicode Default_Ignorable_Code_Point property was not loaded")
    return result


def internal_skeleton(value: str, mappings: dict[str, str], ignorables: set[int]) -> str:
    first = unicodedata.normalize("NFD", value)
    mapped = "".join(
        "" if ord(char) in ignorables else mappings.get(char, char)
        for char in first
    )
    return unicodedata.normalize("NFD", mapped)


def codepoints(value: str | None):
    return None if value is None else [f"{ord(char):04X}" for char in value]


def resolve_display_equivalence(case, mappings, ignorables):
    intended = case["intended_id"]
    resolved = case["resolved_id"]
    label_match = case["displayed_label"] == case["intended_label"]
    if case["display_class"] == "exact":
        if resolved is None or intended != resolved or case["resolution_rule"] != "identity":
            raise ValueError(f"invalid exact fixture: {case['case_id']}")
        if not label_match:
            raise ValueError(f"exact fixture label does not match request: {case['case_id']}")
        return True, internal_skeleton(intended, mappings, ignorables), internal_skeleton(resolved, mappings, ignorables)
    if case["display_class"] == "declared_label_alias":
        if resolved is None or intended == resolved or case["resolution_rule"] != "fixture_label_resolver":
            raise ValueError(f"invalid label-alias fixture: {case['case_id']}")
        if not label_match:
            raise ValueError(f"declared alias does not match requested label: {case['case_id']}")
        left = internal_skeleton(intended, mappings, ignorables)
        right = internal_skeleton(resolved, mappings, ignorables)
        return True, left, right
    if case["display_class"] == "unresolved":
        if case["resolved_id"] is not None or case["resolution_rule"] != "no_resolution":
            raise ValueError(f"unresolved fixture unexpectedly has exact ID: {case['case_id']}")
        left = internal_skeleton(intended, mappings, ignorables)
        right = None if resolved is None else internal_skeleton(resolved, mappings, ignorables)
        return label_match, left, right
    raise ValueError(f"unknown display class: {case['display_class']}")


def evaluate(case, policy, equivalence):
    intended = case["intended_id"]
    resolved = case["resolved_id"]
    fresh = bool(case["fresh"])
    label_match, left_skeleton, right_skeleton = equivalence
    warning = bool(policy == "skeleton_warning_only" and label_match
                   and resolved is not None and intended != resolved
                   and left_skeleton == right_skeleton)
    effect = None
    authority = False
    if policy == "string_only":
        if label_match and resolved is not None:
            effect = resolved
    elif policy == "skeleton_warning_only":
        # Warning is informative only; it neither grants nor denies the effect.
        if label_match and resolved is not None:
            effect = resolved
    elif policy == "exact_fresh_binding":
        if not fresh or resolved is None:
            status = "UNKNOWN_TARGET_DISPLAY_EQUIVALENCE"
        elif resolved != intended:
            status = "DENY_TARGET_MISMATCH"
        else:
            status = "EXACT_FRESH_MATCH"
            effect = resolved
            authority = True
        return status, effect, authority, warning
    else:
        raise ValueError(f"unknown policy: {policy}")
    status = "EFFECT" if effect is not None else "NO_MATCH"
    return status, effect, authority, warning


def build_rows(corpus, mappings, ignorables):
    rows = []
    for case in corpus["cases"]:
        equivalence = resolve_display_equivalence(case, mappings, ignorables)
        label_match, left_skeleton, right_skeleton = equivalence
        for policy in POLICIES:
            status, effect, authority, warning = evaluate(case, policy, equivalence)
            rows.append({
                "case_id": case["case_id"],
                "policy": policy,
                "intended_label_codepoints": codepoints(case["intended_label"]),
                "displayed_label_codepoints": codepoints(case["displayed_label"]),
                "intended_codepoints": codepoints(case["intended_id"]),
                "resolved_codepoints": codepoints(case["resolved_id"]),
                "resolution_rule": case["resolution_rule"],
                "fresh": case["fresh"],
                "requested_and_displayed_label_exact_match": label_match,
                "intended_internal_skeleton_codepoints": codepoints(left_skeleton),
                "resolved_internal_skeleton_codepoints": codepoints(right_skeleton),
                "warning_only": warning,
                "status": status,
                "effect_codepoints": codepoints(effect),
                "authority_admitted": authority,
            })
    return rows


def self_test(corpus, mappings, ignorables):
    known = [
        ("paypal", "pаypаl"),
        ("scope", "ѕсоре"),
        ("paypal", "pay​pal"),
        ("café", "café"),
    ]
    assert all(internal_skeleton(a, mappings, ignorables) ==
               internal_skeleton(b, mappings, ignorables) for a, b in known)
    rows = build_rows(corpus, mappings, ignorables)
    aliases = [case for case in corpus["cases"] if case["display_class"] == "declared_label_alias"]
    skeleton_aliases = [case for case in aliases if internal_skeleton(case["intended_id"], mappings, ignorables)
                        == internal_skeleton(case["resolved_id"], mappings, ignorables)]
    assert len(aliases) == 6 and len(skeleton_aliases) == 5
    assert len(rows) == len(corpus["cases"]) * len(POLICIES)
    grouped = {(r["case_id"], r["policy"]): r for r in rows}
    assert len(grouped) == len(rows)
    for case in corpus["cases"]:
        c = grouped[(case["case_id"], "exact_fresh_binding")]
        if case["fresh"] and case["resolved_id"] == case["intended_id"]:
            assert c["status"] == "EXACT_FRESH_MATCH" and c["authority_admitted"]
        else:
            assert not c["authority_admitted"] and c["effect_codepoints"] is None
    for case_id in ("arabic_exact", "hebrew_exact", "persian_joiner_exact",
                    "japanese_exact", "mixed_script_exact", "bidi_control_exact"):
        assert grouped[(case_id, "exact_fresh_binding")]["authority_admitted"]
    bidi = grouped[("bidi_mismatch_alias", "skeleton_warning_only")]
    assert bidi["status"] == "EFFECT" and bidi["warning_only"]
    assert grouped[("bidi_mismatch_alias", "exact_fresh_binding")]["status"] == "DENY_TARGET_MISMATCH"
    return {"checks": 8, "cases": len(corpus["cases"]), "rows": len(rows)}


def main():
    verify_data_files()
    mappings = parse_confusables(CONFUSABLES_PATH)
    ignorables = parse_default_ignorables(DERIVED_PATH)
    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    if corpus["unicode_version"] != "18.0.0":
        raise ValueError("fixture/data version mismatch")
    if "--self-test" in sys.argv:
        print(json.dumps(self_test(corpus, mappings, ignorables), sort_keys=True))
        return
    rows = build_rows(corpus, mappings, ignorables)
    with OUTPUT_PATH.open("w", encoding="utf-8", newline="\n") as output:
        for row in rows:
            output.write(json.dumps(row, sort_keys=True, ensure_ascii=True,
                                    separators=(",", ":")) + "\n")
    print(json.dumps({"rows": len(rows), "cases": len(corpus["cases"]),
                      "output": OUTPUT_PATH.name,
                      "unicode_data": "18.0.0",
                      "python_ucd": unicodedata.unidata_version}, sort_keys=True))


if __name__ == "__main__":
    main()
