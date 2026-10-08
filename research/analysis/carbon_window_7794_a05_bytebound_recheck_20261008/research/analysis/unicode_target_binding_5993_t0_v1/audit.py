"""Independent raw-only scorer for Issue #5993 T0; does not import simulate.py."""
from __future__ import annotations

import hashlib
import json
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parent
CORPUS = ROOT / "corpus.json"
CONFUSABLES = ROOT / "confusables.txt"
DERIVED = ROOT / "DerivedCoreProperties.txt"
PINNED = {
    "confusables.txt": "6ED3EE967C9DFDF6677D563C9985182FBC50A2EFB7D6059CD57B2E2CE18F5B92",
    "DerivedCoreProperties.txt": "09C928886A178FCAFD93C29E4BD59073A058E5A100B716D425CB563AB50F68C9",
}
POLICIES = ("string_only", "skeleton_warning_only", "exact_fresh_binding")


def check_sources():
    for p in (CONFUSABLES, DERIVED):
        if hashlib.sha256(p.read_bytes()).hexdigest().upper() != PINNED[p.name]:
            raise ValueError("source hash mismatch: " + p.name)


def reference_tables():
    # Different representation/parsing path from the candidate.
    transducer = {}
    for line in CONFUSABLES.read_text(encoding="utf-8").splitlines():
        line = line.partition("#")[0]
        fields = line.split(";")
        if len(fields) < 3 or not fields[0].strip():
            continue
        src = int(fields[0].strip(), 16)
        dst = tuple(int(part, 16) for part in fields[1].split())
        if src in transducer or not dst:
            raise ValueError("ambiguous mapping table")
        transducer[src] = dst
    ignorable = set()
    for line in DERIVED.read_text(encoding="utf-8").splitlines():
        text = line.partition("#")[0]
        if ";" not in text:
            continue
        span, property_name = (item.strip() for item in text.split(";", 1))
        if property_name != "Default_Ignorable_Code_Point":
            continue
        ends = span.split("..")
        lo = int(ends[0], 16)
        hi = int(ends[-1], 16)
        ignorable.update(range(lo, hi + 1))
    if not transducer or not ignorable:
        raise ValueError("empty reference Unicode tables")
    return transducer, ignorable


def reference_key(value, transducer, ignorable):
    normalized = unicodedata.normalize("NFD", value)
    output = []
    for char in normalized:
        cp = ord(char)
        if cp in ignorable:
            continue
        mapped = transducer.get(cp, (cp,))
        output.extend(chr(part) for part in mapped)
    return tuple(ord(char) for char in unicodedata.normalize("NFD", "".join(output)))


def expected(case, policy, transducer, ignorable):
    intended, resolved = case["intended_id"], case["resolved_id"]
    label_match = case["displayed_label"] == case["intended_label"]
    if case["display_class"] == "exact":
        if resolved is None or intended != resolved or not label_match or case["resolution_rule"] != "identity":
            raise ValueError("invalid exact fixture")
    elif case["display_class"] == "declared_label_alias":
        if resolved is None or intended == resolved or not label_match or case["resolution_rule"] != "fixture_label_resolver":
            raise ValueError("invalid declared-label-alias fixture")
    else:
        if resolved is not None or case["resolution_rule"] != "no_resolution":
            raise ValueError("invalid unresolved fixture")
    left = reference_key(intended, transducer, ignorable)
    right = None if resolved is None else reference_key(resolved, transducer, ignorable)
    warning = bool(policy == "skeleton_warning_only" and label_match
                   and resolved is not None and intended != resolved
                   and left == right)
    effect = None
    authority = False
    if policy in ("string_only", "skeleton_warning_only"):
        if label_match and resolved is not None:
            effect = resolved
        status = "EFFECT" if effect is not None else "NO_MATCH"
    elif not case["fresh"] or resolved is None:
        status = "UNKNOWN_TARGET_DISPLAY_EQUIVALENCE"
    elif resolved != intended:
        status = "DENY_TARGET_MISMATCH"
    else:
        status, effect, authority = "EXACT_FRESH_MATCH", resolved, True
    return label_match, warning, status, effect, authority


def expected_record(case, policy, transducer, ignorable):
    label_match, warning, status, effect, authority = expected(case, policy, transducer, ignorable)
    left = reference_key(case["intended_id"], transducer, ignorable)
    right = None if case["resolved_id"] is None else reference_key(case["resolved_id"], transducer, ignorable)
    return {
        "case_id": case["case_id"], "policy": policy,
        "intended_label_codepoints": [f"{ord(ch):04X}" for ch in case["intended_label"]],
        "displayed_label_codepoints": [f"{ord(ch):04X}" for ch in case["displayed_label"]],
        "intended_codepoints": [f"{ord(ch):04X}" for ch in case["intended_id"]],
        "resolved_codepoints": None if case["resolved_id"] is None else [f"{ord(ch):04X}" for ch in case["resolved_id"]],
        "resolution_rule": case["resolution_rule"],
        "fresh": case["fresh"], "requested_and_displayed_label_exact_match": label_match,
        "intended_internal_skeleton_codepoints": [f"{cp:04X}" for cp in left],
        "resolved_internal_skeleton_codepoints": None if right is None else [f"{cp:04X}" for cp in right],
        "warning_only": warning, "status": status,
        "effect_codepoints": None if effect is None else [f"{ord(ch):04X}" for ch in effect],
        "authority_admitted": authority,
    }


def audit(raw_path):
    check_sources()
    transducer, ignorable = reference_tables()
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    expected_keys = {(c["case_id"], p) for c in corpus["cases"] for p in POLICIES}
    seen = {}
    errors = []
    for line_no, line in enumerate(raw_path.read_text(encoding="utf-8").splitlines(), 1):
        try:
            row = json.loads(line)
        except Exception as exc:
            errors.append({"line": line_no, "error": "invalid_json", "detail": str(exc)})
            continue
        key = (row.get("case_id"), row.get("policy"))
        if key not in expected_keys:
            errors.append({"line": line_no, "error": "unexpected_key", "key": key})
            continue
        if key in seen:
            errors.append({"line": line_no, "error": "duplicate_key", "key": key})
            continue
        seen[key] = row

    missing = expected_keys - set(seen)
    for key in sorted(missing):
        errors.append({"error": "missing_key", "key": key})

    cases = {c["case_id"]: c for c in corpus["cases"]}
    counts = Counter()
    for key, row in seen.items():
        case = cases[key[0]]
        policy = key[1]
        label_match, warning, status, effect, authority = expected(case, policy, transducer, ignorable)
        intended = tuple(ord(ch) for ch in case["intended_id"])
        resolved = None if case["resolved_id"] is None else tuple(ord(ch) for ch in case["resolved_id"])
        effect_cps = None if effect is None else tuple(ord(ch) for ch in effect)
        exp_key = reference_key(case["intended_id"], transducer, ignorable)
        exp_res_key = None if case["resolved_id"] is None else reference_key(case["resolved_id"], transducer, ignorable)
        checks = {
            "intended_label_codepoints": [f"{ord(ch):04X}" for ch in case["intended_label"]],
            "displayed_label_codepoints": [f"{ord(ch):04X}" for ch in case["displayed_label"]],
            "intended_codepoints": list(f"{cp:04X}" for cp in intended),
            "resolved_codepoints": None if resolved is None else [f"{cp:04X}" for cp in resolved],
            "resolution_rule": case["resolution_rule"],
            "fresh": case["fresh"],
            "requested_and_displayed_label_exact_match": label_match,
            "intended_internal_skeleton_codepoints": [f"{cp:04X}" for cp in exp_key],
            "resolved_internal_skeleton_codepoints": None if exp_res_key is None else [f"{cp:04X}" for cp in exp_res_key],
            "warning_only": warning,
            "status": status,
            "effect_codepoints": None if effect_cps is None else [f"{cp:04X}" for cp in effect_cps],
            "authority_admitted": authority,
        }
        for field, expected_value in checks.items():
            if row.get(field) != expected_value:
                errors.append({"key": key, "error": "field_mismatch", "field": field,
                               "expected": expected_value, "observed": row.get(field)})
        counts[policy + ":" + status] += 1
        if effect_cps is not None and effect_cps != intended:
            counts[policy + ":wrong_target_effect"] += 1
        if authority and (effect_cps is None or effect_cps != intended or not case["fresh"]):
            errors.append({"key": key, "error": "unsafe_authority"})

    spoof_ids = {c["case_id"] for c in corpus["cases"] if c["display_class"] == "declared_label_alias"}
    if not spoof_ids:
        errors.append({"error": "no_declared_label_aliases"})
    alias_cases = [c for c in corpus["cases"] if c["display_class"] == "declared_label_alias"]
    skeleton_aliases = [c for c in alias_cases
                        if reference_key(c["intended_id"], transducer, ignorable)
                        == reference_key(c["resolved_id"], transducer, ignorable)]
    if len(alias_cases) != 6 or len(skeleton_aliases) != 5:
        errors.append({"error": "alias_fixture_gate", "aliases": len(alias_cases),
                       "skeleton_aliases": len(skeleton_aliases),
                       "expected_aliases": 6, "expected_skeleton_aliases": 5})
    for policy in POLICIES:
        wrong = counts[policy + ":wrong_target_effect"]
        if policy == "exact_fresh_binding" and wrong != 0:
            errors.append({"error": "exact_binding_wrong_target_nonzero", "count": wrong})
    benign_exact = [c for c in corpus["cases"] if c["display_class"] == "exact" and c["fresh"]]
    for case in benign_exact:
        row = seen.get((case["case_id"], "exact_fresh_binding"))
        if row is None or not row.get("authority_admitted"):
            errors.append({"error": "benign_exact_false_refusal", "case": case["case_id"]})
    return {
        "status": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT",
        "rows": len(seen),
        "expected_rows": len(expected_keys),
        "cases": len(corpus["cases"]),
        "declared_label_aliases": len(spoof_ids),
        "benign_exact_accepted": len(benign_exact),
        "counts": dict(sorted(counts.items())),
        "errors": errors,
        "scope": "synthetic identifier/resolver semantics only; no GUI/font/app effect",
    }


def self_test():
    # These are pre-freeze wiring/corruption checks, not formal result audits.
    check_sources()
    transducer, ignorable = reference_tables()
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    cases = {case["case_id"]: case for case in corpus["cases"]}
    assert reference_key("paypal", transducer, ignorable) == reference_key("pаypаl", transducer, ignorable)
    assert reference_key("scope", transducer, ignorable) == reference_key("ѕсоре", transducer, ignorable)
    assert reference_key("paypal", transducer, ignorable) == reference_key("pay​pal", transducer, ignorable)
    assert reference_key("café", transducer, ignorable) == reference_key("café", transducer, ignorable)
    controls = [expected_record(case, policy, transducer, ignorable)
                for case in corpus["cases"] for policy in POLICIES]
    with TemporaryDirectory(prefix="5993-audit-construct-") as temp:
        path = Path(temp) / "rows.jsonl"

        def run(rows):
            path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
            return audit(path)

        assert run(controls)["status"] == "PASS_METHOD_SCOPED"
        assert run(controls[:-1])["status"] == "FAIL_AUDIT"       # missing row
        assert run(controls + [controls[0]])["status"] == "FAIL_AUDIT"  # duplicate row
        bad_effect = [dict(row) for row in controls]
        exact = next(row for row in bad_effect if row["case_id"] == "ascii_exact" and row["policy"] == "exact_fresh_binding")
        exact["effect_codepoints"] = [ord("X")]
        assert run(bad_effect)["status"] == "FAIL_AUDIT"
        bad_authority = [dict(row) for row in controls]
        mismatch = next(row for row in bad_authority if row["case_id"] == "cyrillic_a_paypal" and row["policy"] == "exact_fresh_binding")
        mismatch["authority_admitted"] = True
        assert run(bad_authority)["status"] == "FAIL_AUDIT"
        bad_label = [dict(row) for row in controls]
        label = next(row for row in bad_label if row["case_id"] == "bidi_mismatch_alias" and row["policy"] == "string_only")
        label["displayed_label_codepoints"] = [ord("X")]
        assert run(bad_label)["status"] == "FAIL_AUDIT"
        no_warning = [dict(row) for row in controls]
        warning_row = next(row for row in no_warning if row["case_id"] == "bidi_mismatch_alias" and row["policy"] == "skeleton_warning_only")
        warning_row["warning_only"] = False
        assert run(no_warning)["status"] == "FAIL_AUDIT"
    return {"construction_checks": 11, "status": "PASS"}


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        print(json.dumps(self_test(), sort_keys=True))
    else:
        raw = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "candidate.jsonl"
        print(json.dumps(audit(raw), sort_keys=True, ensure_ascii=False))
