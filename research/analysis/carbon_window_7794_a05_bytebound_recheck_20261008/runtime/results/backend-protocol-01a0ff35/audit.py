"""Raw-only finite oracle; imports neither registry nor matrix generator."""
import copy
import hashlib
import itertools
import json
from pathlib import Path
import sys


def audit(record, baseline=False):
    expected_states = list(itertools.product(("missing", "noncallable", "callable"), repeat=4))
    rows = record.get("rows")
    if type(rows) is not list or len(rows) != 81:
        raise ValueError("all 81 rows required")
    if record.get("schema") != "backend-factory-matrix-v1":
        raise ValueError("schema mismatch")
    accepted = 0
    for row, states in zip(rows, expected_states):
        if row.get("states") != list(states):
            raise ValueError("row identity/order mismatch")
        complete = states == ("callable",) * 4
        if baseline:
            want = {"missing": "AttributeError", "noncallable": "TypeError", "callable": "accepted"}[states[0]]
            probe_count = int(states[0] == "callable")
        else:
            want = "accepted" if complete else "contract_rejected"
            probe_count = int(complete)
        if row.get("outcome") != want:
            raise ValueError("admission mismatch")
        counts = row.get("calls")
        if type(counts) is not dict or set(counts) != {"probe", "observe", "execute", "release_all"}:
            raise ValueError("call inventory mismatch")
        if any(type(n) is not int for n in counts.values()):
            raise ValueError("call count must be exact integer")
        if counts != {"probe": probe_count, "observe": 0, "execute": 0, "release_all": 0}:
            raise ValueError("unexpected probe or backend I/O")
        accepted += int(want == "accepted")
    return dict(rows=len(rows), accepted=accepted, invalid_accepted=accepted-1)


def main():
    here = Path(__file__).resolve().parent
    before = json.loads((here / "baseline-matrix-02.stdout.txt").read_bytes())
    after = json.loads((here / "repaired-matrix.stdout.txt").read_bytes())
    summary = dict(baseline=audit(before, True), repaired=audit(after))
    original = []
    altered = copy.deepcopy(after); altered["rows"].pop(); original.append(altered)
    altered = copy.deepcopy(after); altered["rows"][1] = altered["rows"][0]; original.append(altered)
    altered = copy.deepcopy(after); altered["rows"][0]["outcome"] = "accepted"; original.append(altered)
    altered = copy.deepcopy(after); altered["rows"][0]["calls"]["probe"] = 1; original.append(altered)
    altered = copy.deepcopy(after); altered["rows"][-1]["calls"]["release_all"] = 1; original.append(altered)
    altered = copy.deepcopy(after); altered["rows"][0]["calls"]["probe"] = False; original.append(altered)
    rejected = 0
    for record in original:
        try:
            audit(record)
        except ValueError:
            rejected += 1
    if rejected != len(original):
        raise ValueError("corruption control accepted")
    backend = here.parents[1] / "kernel/backend.py"
    captured_source = (here / "source-repaired.py").read_bytes()
    if after["backend_sha256"] != hashlib.sha256(captured_source).hexdigest():
        raise ValueError("repaired source capture mismatch")
    if backend.read_bytes().replace(b"\r\n", b"\n") != captured_source.replace(b"\r\n", b"\n"):
        raise ValueError("repaired source changed")
    baseline_source = (here / "source-baseline.py").read_bytes()
    if before["backend_sha256"] != hashlib.sha256(baseline_source).hexdigest():
        raise ValueError("baseline source capture mismatch")
    summary.update(corruptions_rejected=rejected, imports_registry=False,
                   decision="PASS_FACTORY_ADMISSION_SCOPED")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
