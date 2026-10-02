from __future__ import annotations

import base64
import hashlib
import io
import json
import lzma
import re
import subprocess
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "candidate.raw.json"
PREFIX = "research/integration/x11_reconnect_key_state_2107_v1/"
EDGE_KEY = re.compile(r"(causal|parent|message[_-]?(id|send|receive)|send[_-]?id|receive[_-]?id)", re.I)


def git_blob(root: Path, commit: str, path: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(root), "show", f"{commit}:{path}"])


def archive_from_git(root: Path, commit: str, freeze: dict) -> tuple[dict, bytes, tarfile.TarFile]:
    meta = json.loads(git_blob(root, commit, PREFIX + "EVIDENCE_BASE64.json"))
    if meta["archive_sha256"] != freeze["archive_sha256"] or meta["archive_bytes"] != freeze["archive_bytes"]:
        raise ValueError("FROZEN_ARCHIVE_METADATA_MISMATCH")
    chunks = []
    for item in meta["parts"]:
        raw = git_blob(root, commit, PREFIX + item["path"])
        chunk = raw.decode("ascii").strip()
        expected_part = freeze["archive_parts"].get(item["path"])
        if expected_part != item["sha256"] or len(chunk) != item["chars"] or hashlib.sha256(chunk.encode("ascii")).hexdigest() != item["sha256"]:
            raise ValueError(f"PART_INTEGRITY:{item['path']}")
        chunks.append(chunk)
    archive = base64.b64decode("".join(chunks), validate=True)
    if len(archive) != meta["archive_bytes"] or hashlib.sha256(archive).hexdigest() != meta["archive_sha256"]:
        raise ValueError("ARCHIVE_INTEGRITY")
    tar = tarfile.open(fileobj=io.BytesIO(lzma.decompress(archive)), mode="r:")
    return meta, archive, tar


def jsonl(raw: bytes) -> list[dict]:
    return [json.loads(line) for line in raw.splitlines() if line.strip()]


def recursive_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from recursive_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from recursive_keys(child)


def inspect(root: Path, commit: str, freeze: dict) -> dict:
    meta, archive, tar = archive_from_git(root, commit, freeze)
    members = {m.name: m for m in tar.getmembers() if m.isfile()}
    case_paths = sorted(n for n in members if "/formal_v2/" in n and n.endswith("/case.json"))
    cases = [(name, json.loads(tar.extractfile(members[name]).read())) for name in case_paths]
    selected = [(name, case) for name, case in cases
                if case.get("policy") == "REBOOTSTRAP_ON_RECONNECT"
                and case.get("scenario") in {"DISCONNECT_PRESS", "DISCONNECT_RELEASE"}]
    rows = []
    for name, case in selected:
        base = name.rsplit("/", 1)[0]
        observer_raw = tar.extractfile(members[base + "/observer2.jsonl"]).read()
        app_raw = tar.extractfile(members[base + "/app/app_events.jsonl"]).read()
        observer_events, app_events = jsonl(observer_raw), jsonl(app_raw)
        event_keys = sorted({k for e in observer_events + app_events for k in e})
        edge_fields = sorted({k for k in recursive_keys(case) if EDGE_KEY.search(k)})
        bootstrap = case.get("bootstrap_packet") or {}
        epoch = case.get("epoch")
        rows.append({
            "case_path": name,
            "scenario": case.get("scenario"),
            "rep": case.get("rep"),
            "case_epoch": epoch,
            "bootstrap_epoch": bootstrap.get("epoch"),
            "bootstrap_epoch_matches": bootstrap.get("epoch") == epoch,
            "observer_event_count": len(observer_events),
            "observer_raw_matches_aggregate": observer_events == case.get("observer2_events"),
            "observer_event_epochs_match": all(e.get("epoch") == epoch for e in observer_events),
            "app_event_count": len(app_events),
            "app_raw_matches_aggregate": app_events == case.get("app_events"),
            "event_fields": event_keys,
            "explicit_causal_edge_fields": edge_fields,
            "monotonic_timestamps_both_streams": all("mono_ns" in e for e in observer_events + app_events),
            "final_value": case.get("final_value"),
            "final_neutral": case.get("final_neutral"),
        })
    all_raw_match = all(r["observer_raw_matches_aggregate"] and r["app_raw_matches_aggregate"] for r in rows)
    all_epoch_match = all(r["bootstrap_epoch_matches"] and r["observer_event_epochs_match"] for r in rows)
    edge_rows = [r for r in rows if r["explicit_causal_edge_fields"]]
    observer_source = git_blob(root, commit, PREFIX + "observer.py")
    app_source = git_blob(root, commit, PREFIX + "app.py")
    source_hashes_match = (hashlib.sha256(observer_source).hexdigest() == freeze["source_hashes"]["observer.py"]
                           and hashlib.sha256(app_source).hexdigest() == freeze["source_hashes"]["app.py"])
    inventory_ok = len(members) == freeze["expanded_file_count"] and len(cases) == 24 and len(rows) == freeze["selected_cases"]["expected_rows"]
    disposition = "STOP_TRACE_INTEGRITY_OR_INVENTORY" if not inventory_ok or not all_raw_match or not all_epoch_match or not source_hashes_match else "PASS_TRACE_CUT_APPLICABILITY" if len(edge_rows) == len(rows) else "HOLD_CAUSAL_EDGE_PROVENANCE_MISSING" if rows and not edge_rows else "HOLD_NO_ELIGIBLE_TRACE"
    return {
        "schema": "blackstart-trace-applicability-candidate-v1",
        "source_commit": commit,
        "archive_sha256": hashlib.sha256(archive).hexdigest(),
        "archive_bytes": len(archive),
        "expanded_file_count": len(members),
        "formal_case_count": len(cases),
        "frozen_inventory_ok": inventory_ok,
        "selected_positive_case_count": len(rows),
        "selected_rows": rows,
        "raw_aggregates_match": all_raw_match,
        "bootstrap_epochs_match": all_epoch_match,
        "explicit_cross_source_edge_rows": len(edge_rows),
        "observer_source_sha256": hashlib.sha256(observer_source).hexdigest(),
        "app_source_sha256": hashlib.sha256(app_source).hexdigest(),
        "frozen_source_hashes_match": source_hashes_match,
        "observer_uses_one_display_for_bootstrap_and_events": observer_source.count(b"display.Display()") == 1 and observer_source.index(b"d.query_keymap()") < observer_source.index(b"while True:") and b"d.pending_events()" in observer_source,
        "app_emits_monotonic_state_and_event_records": b"time.monotonic_ns()" in app_source,
        "disposition": disposition,
    }


def main() -> None:
    if OUT.exists():
        raise SystemExit("STOP_OUTPUT_ALREADY_EXISTS")
    root = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    for name, expected in freeze["analysis_sources_sha256"].items():
        if hashlib.sha256((HERE / name).read_bytes()).hexdigest() != expected:
            raise SystemExit(f"STOP_FROZEN_ANALYSIS_SOURCE_CHANGED:{name}")
    result = inspect(root, freeze["source_commit"], freeze)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
