from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


FIXTURE_SHA = "5531e1296e31064da7661138f6ae9036e473b5c953ebd82b3f1ce28a9409fd61"
SCHEDULE_SHA = "90c2d136dfe7e429bfdc504c12fff51e4ad141030080b897d11249a5f28151cd"
FORMAL_MANIFEST_SHA = "1584edb3a45202b3e816d2a9735708265da279fd4e18d8680fded7756cc3855"
ALLOCATION = "temporal-stream-resume-20260926-01"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def co_states(events: list[dict]) -> list[str]:
    status, current, anchor = "PENDING", None, None
    labels: set[str] = set()
    out = []
    for event in events:
        tick = event["server_ms"]
        if status != "PENDING":
            out.append(status)
            continue
        if type(tick) is not int or (current is not None and tick < current):
            status = "UNKNOWN"
        elif current is None:
            current = tick
        elif tick > current:
            if anchor is not None and tick > anchor + 80:
                status = "EXPIRED"
            else:
                current, labels = tick, set()
        if status == "PENDING":
            if event["label"] != "H":
                labels.add(event["label"])
            if anchor is None and "A" in labels:
                anchor = tick
            if anchor is not None and anchor <= tick <= anchor + 80 and "B" in labels:
                status = "SATISFIED"
        out.append(status)
    return out


def ordered_states(events: list[dict], strict: bool) -> list[str]:
    status, previous, next_ordinal, anchor = "PENDING", None, 1, None
    out = []
    for event in events:
        if status != "PENDING":
            out.append(status)
            continue
        invalid = (
            set(event) != {"epoch", "ordinal", "server_ms", "label"}
            or type(event["ordinal"]) is not int
            or event["ordinal"] != next_ordinal
            or type(event["server_ms"]) is not int
            or event["label"] not in {"A", "B", "H"}
            or (previous is not None and event["server_ms"] < previous)
        )
        if invalid:
            status = "UNKNOWN"
            out.append(status)
            continue
        tick, ordinal = event["server_ms"], event["ordinal"]
        previous, next_ordinal = tick, next_ordinal + 1
        if anchor is not None and tick - anchor[0] > 80:
            status = "EXPIRED"
        elif event["label"] == "A" and anchor is None:
            anchor = (tick, ordinal)
        elif event["label"] == "B" and anchor is not None:
            if (tick > anchor[0]) if strict else (ordinal > anchor[1]):
                status = "SATISFIED"
        out.append(status)
    return out


def oracle(events: list[dict]) -> list[dict]:
    values = zip(co_states(events), ordered_states(events, True), ordered_states(events, False))
    return [dict(co_timestamp=a, strict_time=b, ordered=c) for a, b, c in values]


def check_manifest(evidence: Path, errors: list[str]) -> None:
    manifest_path = evidence / "ARTIFACT_MANIFEST.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"artifact manifest unreadable: {type(exc).__name__}")
        return
    for item in manifest.get("artifacts", []):
        path = evidence / item["path"]
        if not path.is_file():
            errors.append(f"manifest missing {item['path']}")
        elif path.stat().st_size != item["bytes"] or sha256(path) != item["sha256"]:
            errors.append(f"manifest identity {item['path']}")


def child(receipt: object, name: str, expected_rc: int, errors: list[str], case_id: int):
    if not isinstance(receipt, dict):
        errors.append(f"{name} receipt missing case {case_id}")
        return {}
    if receipt.get("returncode") != expected_rc:
        errors.append(f"{name} returncode case {case_id}")
    raw = receipt.get("stdout")
    try:
        decoded = json.loads(raw)
    except Exception:
        decoded = None
    if decoded is None or decoded != receipt.get("parsed"):
        errors.append(f"{name} stdout/parsed mismatch case {case_id}")
    if receipt.get("stderr") != "":
        errors.append(f"{name} stderr case {case_id}")
    return receipt.get("parsed") if isinstance(receipt.get("parsed"), dict) else {}


def audit(source: Path, evidence: Path, expected_manifest_sha: str | None = None) -> dict:
    errors: list[str] = []
    source_manifest = json.loads((source / "SOURCE_HASHES.json").read_text(encoding="utf-8"))
    for name, item in source_manifest.items():
        path = source / name
        if not path.is_file() or path.stat().st_size != item["bytes"] or sha256(path) != item["sha256"]:
            errors.append(f"source identity {name}")
    if sha256(source / "fixtures.json") != FIXTURE_SHA:
        errors.append("fixture commitment")
    if sha256(source / "SCHEDULE.json") != SCHEDULE_SHA:
        errors.append("schedule commitment")
    check_manifest(evidence, errors)
    manifest_sha = sha256(evidence / "ARTIFACT_MANIFEST.json")
    if expected_manifest_sha is not None and manifest_sha != expected_manifest_sha:
        errors.append("formal artifact manifest commitment")

    fixtures = json.loads((source / "fixtures.json").read_text(encoding="utf-8"))
    schedule = json.loads((source / "SCHEDULE.json").read_text(encoding="utf-8"))
    if len(fixtures) != 24 or len(schedule) != 54:
        errors.append("source denominator")

    cases: list[dict] = []
    outer_receipts = []
    for batch in range(6):
        path = evidence / f"BATCH{batch}.json"
        outer_path = evidence / f"OUTER_BATCH{batch}.json"
        if not path.is_file() or not outer_path.is_file():
            errors.append(f"batch artifacts {batch}")
            continue
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
            outer = json.loads(outer_path.read_text(encoding="utf-8"))
        except Exception:
            errors.append(f"batch JSON {batch}")
            continue
        if doc.get("allocation") != ALLOCATION or doc.get("batch") != batch:
            errors.append(f"batch identity {batch}")
        if doc.get("range") != [batch * 9, batch * 9 + 8] or doc.get("complete") is not True:
            errors.append(f"batch range/completion {batch}")
        if outer.get("batch") != batch or outer.get("docker_exit_code") != 0:
            errors.append(f"Docker outer exit {batch}")
        try:
            outer_stdout = json.loads(outer["output"])
        except Exception:
            outer_stdout = None
        if outer_stdout != {"batch": batch, "complete": True, "rows": 9}:
            errors.append(f"Docker outer stdout {batch}")
        outer_receipts.append(outer)
        rows = doc.get("rows", [])
        if len(rows) != 9:
            errors.append(f"batch denominator {batch}")
        cases.extend(rows)

    if len(cases) != 54:
        errors.append("case denominator")
    observed_ids = []
    candidate_ok = comparator_disagreements = corruption_refusals = 0
    for index, outer_row in enumerate(cases):
        if index >= len(schedule):
            break
        request = schedule[index]
        parsed = outer_row.get("parsed")
        observed_ids.append(outer_row.get("case_id"))
        if outer_row.get("timeout") is not False or outer_row.get("returncode") != 0:
            errors.append(f"case process receipt {index}")
        try:
            stdout_parsed = json.loads(outer_row.get("stdout", ""))
        except Exception:
            stdout_parsed = None
        if stdout_parsed != parsed or not isinstance(parsed, dict):
            errors.append(f"case stdout/parsed mismatch {index}")
            continue
        cid = request["case_id"]
        if outer_row.get("case_id") != cid or parsed.get("case_id") != cid:
            errors.append(f"case identity {cid}")
        for key in ("fixture_index", "cut", "epoch", "prefix", "suffix", "mutation"):
            if parsed.get(key) != request.get(key):
                errors.append(f"schedule binding {key} case {cid}")
        fi, cut = request["fixture_index"], request["cut"]
        if not 0 <= fi < len(fixtures):
            errors.append(f"fixture index case {cid}")
            continue
        events = fixtures[fi]["events"]
        if fixtures[fi]["epoch"] != request["epoch"] or request["prefix"] != events[:cut] or request["suffix"] != events[cut:]:
            errors.append(f"fixture slice case {cid}")
        if parsed.get("authority") != "none" or parsed.get("task_success") is not None or parsed.get("input_dispatched") is not False:
            errors.append(f"case authority {cid}")

        prep = child(parsed.get("prepare"), "prepare", 0, errors, cid)
        if prep.get("status") != "OK" or prep.get("authority") != "none" or prep.get("task_success") is not None or prep.get("input_dispatched") is not False:
            errors.append(f"prepare semantics {cid}")

        mutation = request.get("mutation")
        expected_rc = 3 if mutation else 0
        candidate = child(parsed.get("candidate"), "candidate", expected_rc, errors, cid)
        if candidate.get("authority") != "none" or candidate.get("task_success") is not None or candidate.get("input_dispatched") is not False:
            errors.append(f"candidate authority {cid}")
        if mutation:
            corruption_refusals += 1
            if candidate.get("status") != "REFUSE_CHECKPOINT" or candidate.get("suffix") != []:
                errors.append(f"corruption refusal {cid}")
            if parsed.get("comparator") is not None:
                errors.append(f"corruption comparator present {cid}")
            continue

        candidate_ok += 1
        comparator = child(parsed.get("comparator"), "comparator", 0, errors, cid)
        if comparator.get("authority") != "none" or comparator.get("task_success") is not None or comparator.get("input_dispatched") is not False:
            errors.append(f"comparator authority {cid}")
        prefix, suffix = request["prefix"], request["suffix"]
        expected = oracle(events)
        expected_suffix = expected[cut:]
        if candidate.get("status") != "OK" or candidate.get("suffix") != expected_suffix:
            errors.append(f"candidate oracle {cid}")
        if comparator.get("status") != "OK":
            errors.append(f"comparator status {cid}")
        elif comparator.get("suffix") != expected_suffix:
            comparator_disagreements += 1
        checkpoint = parsed.get("checkpoint", {})
        prefix_sha = hashlib.sha256(canonical(prefix)).hexdigest()
        historical = expected[cut - 1]
        if (
            checkpoint.get("epoch") != request["epoch"]
            or checkpoint.get("last_ordinal") != cut
            or checkpoint.get("last_tick") != prefix[-1]["server_ms"]
            or checkpoint.get("prefix_sha256") != prefix_sha
            or checkpoint.get("historical_result") != historical
        ):
            errors.append(f"checkpoint binding {cid}")

    if observed_ids != list(range(54)):
        errors.append("case ID sequence")
    if candidate_ok != 48 or corruption_refusals != 6 or comparator_disagreements <= 0 or len({x.get("fixture_index") for x in schedule[:48]}) != 24:
        errors.append("scientific denominator/discriminator")
    return {
        "errors": errors,
        "rows": len(cases),
        "candidate_ok": candidate_ok,
        "comparator_disagreements": comparator_disagreements,
        "corruption_refusals": corruption_refusals,
        "docker_batch_receipts": len(outer_receipts),
        "artifact_manifest_sha256": manifest_sha,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--expected-manifest-sha256")
    args = parser.parse_args()
    result = audit(args.source, args.evidence, args.expected_manifest_sha256)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if not result["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
