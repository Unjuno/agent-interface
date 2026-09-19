from __future__ import annotations
import argparse, hashlib, json, tarfile, tempfile
from pathlib import Path
from validator import classify, identity_from_context

TASK = "INTEGRATED-RECOVERY-EPISTEMIC-SURFACE-KEY-20260917-001"
EXPECTED = {
    "855": {
        "sha256": "46f08082f3bd58ed67b9a8a16d3fe26c10774d6d7ead246202a10c40e724e9ae",
        "bytes": 10012,
        "backend": "x11",
    },
    "864": {
        "sha256": "5c7725f878028e620a4edf975fe890b0b2d8fda0071cd286a3c70163ca4d96d6",
        "bytes": 10652,
        "backend": "x11",
    },
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_cases(archive: Path, cohort: str):
    exp = EXPECTED[cohort]
    if archive.stat().st_size != exp["bytes"] or sha256(archive) != exp["sha256"]:
        raise RuntimeError(f"{cohort}:archive_identity_mismatch")
    with tempfile.TemporaryDirectory(prefix=f"ai881-{cohort}-") as td:
        with tarfile.open(archive, "r:xz") as tf:
            tf.extractall(td)
        root = Path(td)
        report = (root / "REPORT.md").read_text()
        if "X11" not in report:
            raise RuntimeError(f"{cohort}:backend_provenance_missing")
        paths = sorted((root / "cases").glob("*/case.json"))
        if len(paths) != 8:
            raise RuntimeError(f"{cohort}:case_count:{len(paths)}")
        rows = []
        for p in paths:
            raw = p.read_bytes()
            d = json.loads(raw)
            rows.append((d, hashlib.sha256(raw).hexdigest()))
        return rows


def make_receipt(ctx: dict, backend: str, form: str):
    return {
        "receipt_form": form,
        "identity": identity_from_context(ctx, backend=backend),
        "authority": "none",
        "task_input_granted": False,
        "action_admission_eligible": False,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--formal", action="store_true")
    ap.add_argument("--focus-archive", required=True)
    ap.add_argument("--modal-archive", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if not a.formal:
        raise SystemExit("formal flag required; construction uses test_controls.py")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    marker = out / "FORMAL_INVOCATION.json"
    if marker.exists() or (out / "rows.jsonl").exists() or (out / "RESULT.json").exists():
        raise SystemExit("formal output already exists; rerun forbidden")
    marker.write_text(json.dumps({"task": TASK, "formal_invocations": 1, "formal_reruns": 0}, sort_keys=True, indent=2)+"\n")

    archives = {"855": Path(a.focus_archive), "864": Path(a.modal_archive)}
    rows = []
    archive_receipts = {}
    for cohort in ("855", "864"):
        archive_receipts[cohort] = {
            "sha256": sha256(archives[cohort]),
            "bytes": archives[cohort].stat().st_size,
        }
        for d, case_sha in load_cases(archives[cohort], cohort):
            source = d["source"]
            current = d["admission"]
            current_identity = identity_from_context(current, backend=EXPECTED[cohort]["backend"])
            for form, ctx in (("stale_source", source), ("fresh_current", current)):
                receipt = make_receipt(ctx, EXPECTED[cohort]["backend"], form)
                verdict = classify(receipt, current_identity)
                rows.append({
                    "cohort": cohort,
                    "case_id": d["case_id"],
                    "case_sha256": case_sha,
                    "predecessor_policy": d["policy"],
                    "receipt": receipt,
                    "current_identity": current_identity,
                    **verdict,
                    "authority": "none",
                    "task_input_granted": False,
                    "action_admission_eligible": False,
                })
    rows.sort(key=lambda r: (r["cohort"], r["case_id"], r["receipt"]["receipt_form"]))
    (out / "rows.jsonl").write_text("".join(json.dumps(r, sort_keys=True, separators=(",", ":"))+"\n" for r in rows))
    counts = {}
    for r in rows:
        counts[r["classification"]] = counts.get(r["classification"], 0) + 1
    result = {
        "task": TASK,
        "formal_invocations": 1,
        "formal_reruns": 0,
        "formal_rows": len(rows),
        "archive_receipts": archive_receipts,
        "classification_counts": counts,
        "authority_none": sum(r["authority"] == "none" for r in rows),
        "task_input_false": sum(r["task_input_granted"] is False for r in rows),
        "action_admission_false": sum(r["action_admission_eligible"] is False for r in rows),
        "rows_sha256": sha256(out / "rows.jsonl"),
    }
    (out / "RESULT.json").write_text(json.dumps(result, sort_keys=True, indent=2)+"\n")
    print(json.dumps(result, sort_keys=True))

if __name__ == "__main__":
    main()
