"""Host-only construction check for #5666; not a formal GUI/replay result."""

import hashlib
import json


ORIGINAL = ("setup", "noise", "observe", "grant", "act", "release")
REQUIRED = frozenset(("setup", "observe", "grant", "act", "release"))
OPTIONAL = ("noise",)
FINGERPRINT = ("WRONG_TARGET_EFFECT", "act", "wrong-target")


def simulate(trace):
    present = set(trace)
    if "act" not in present:
        return (0, ("NO_ACTION", None, None))
    if not {"setup", "observe", "grant"}.issubset(present):
        return (1, ("AUTHORITY_OR_SETUP_GAP", "act", "no-effect"))
    if "release" not in present:
        return (1, ("HELD_INPUT_LEAK", "release", "unknown-effect"))
    return (1, FINGERPRINT)


def legal(trace):
    present = set(trace)
    if not REQUIRED.issubset(present) or len(present) != len(trace):
        return False
    if not present.issubset(set(ORIGINAL)):
        return False
    # A reduced trace must retain the original causal order, not just node names.
    return tuple(x for x in ORIGINAL if x in present) == trace


def check():
    assert legal(ORIGINAL)
    original_exit, original_fp = simulate(ORIGINAL)
    assert (original_exit, original_fp) == (1, FINGERPRINT)
    reduced = tuple(x for x in ORIGINAL if x != "noise")
    assert legal(reduced) and simulate(reduced) == (1, FINGERPRINT)

    # A naive exit-code-only reducer can accept a different failure.
    missing_grant = tuple(x for x in reduced if x != "grant")
    assert simulate(missing_grant)[0] == original_exit
    assert simulate(missing_grant)[1] != original_fp
    assert not legal(missing_grant)

    # Mandatory release cannot be removed even if another failure stays visible.
    missing_release = tuple(x for x in reduced if x != "release")
    assert simulate(missing_release)[0] == original_exit
    assert simulate(missing_release)[1] != original_fp
    assert not legal(missing_release)

    reordered = ("setup", "observe", "act", "grant", "release")
    assert set(reordered) == set(reduced)
    assert not legal(reordered)

    # One-minimal only under this frozen legal grammar.
    legal_deletions = [tuple(x for x in reduced if x != y) for y in reduced]
    assert not any(legal(t) and simulate(t) == (1, FINGERPRINT) for t in legal_deletions)
    return {
        "scope": "host-only synthetic construction; no container/model/GUI/replay",
        "original": list(ORIGINAL),
        "reduced": list(reduced),
        "fingerprint": list(FINGERPRINT),
        "exit_only_wrong_failure_rejected": True,
        "authority_and_release_deletion_rejected": True,
        "reordered_authority_rejected": True,
        "one_minimal_under_declared_grammar": True,
    }


if __name__ == "__main__":
    result = check()
    blob = json.dumps(result, sort_keys=True).encode("utf-8")
    print(json.dumps({"result": result, "result_sha256": hashlib.sha256(blob).hexdigest()}, indent=2))

