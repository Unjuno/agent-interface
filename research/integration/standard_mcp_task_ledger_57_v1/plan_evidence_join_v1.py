"""Cross-artifact checks for provider-authored Calc plan lineage.

This is a small evidence join, not an execution or authenticity mechanism.
Callers must first verify raw artifact hashes against their retained manifest.
"""

from __future__ import annotations

import hashlib
import json

from ledger import LedgerValidationError


def _fail(message):
    raise LedgerValidationError(message)


def canonical_plan_sha256(plan):
    """Return the Calc symbolic-plan digest used by CalcTaskArtifact."""
    if type(plan) is not dict:
        _fail("provider plan must be a JSON object")
    try:
        encoded = json.dumps(plan, sort_keys=True, separators=(",", ":"),
                             allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise LedgerValidationError("provider plan is not finite JSON") from error
    return hashlib.sha256(encoded).hexdigest()


def _unique_index(rows, key, label):
    if type(rows) is not list:
        _fail(f"{label} must be an explicit list")
    indexed = {}
    for row in rows:
        if type(row) is not dict:
            _fail(f"{label} rows must be objects")
        value = row.get(key)
        if type(value) is not str or not value or value in indexed:
            _fail(f"{label} has a missing or duplicate {key}")
        indexed[value] = row
    return indexed


def validate_plan_evidence_join(value):
    """Join cold/repair provider plans to public calls, custody and scoring.

    Shape is deliberately explicit. ``raw_generation`` is parsed provider
    output from the already-retained raw response; ``prepare_receipt`` is the
    public prepare result and its exact submitted arguments; ``execution``
    binds the compiled result and post-close verifier to that prepared call.
    Warm rows carry source task/digest lineage while requiring fresh task,
    call, owner and verifier identities.
    """
    if type(value) is not dict or set(value) != {"schema", "rows"}:
        _fail("plan evidence join requires schema and rows")
    if value["schema"] != "agent-interface/calc-plan-evidence-join-v1":
        _fail("unsupported plan evidence join schema")
    rows = value["rows"]
    if type(rows) is not list or len(rows) < 1:
        _fail("join requires at least one observed task row")
    by_task = _unique_index(rows, "task_id", "task rows")
    if len(by_task) != len(rows):
        _fail("task IDs must be unique")

    modes = [row.get("mode") for row in rows]
    if modes[0] != "cold" or any(mode not in {
            "cold", "warm", "repair", "post_repair_warm"} for mode in modes):
        _fail("rows must begin with cold and use known lifecycle modes")
    if modes.count("cold") != 1 or modes.count("repair") > 1:
        _fail("horizon permits one cold generation and at most one repair")
    repair_positions = [index for index, mode in enumerate(modes) if mode == "repair"]
    if repair_positions and repair_positions[0] < 2:
        _fail("repair requires at least one warm task after cold")
    if any(mode == "post_repair_warm" for mode in modes) and not repair_positions:
        _fail("post-repair reuse requires a repair task")
    if repair_positions:
        repair_at = repair_positions[0]
        if any(mode != "warm" for mode in modes[1:repair_at]):
            _fail("pre-repair tasks must be warm reuse")
        if any(mode != "post_repair_warm" for mode in modes[repair_at + 1:]):
            _fail("post-repair tasks must reuse the repaired plan")
    elif any(mode != "warm" for mode in modes[1:]):
        _fail("tasks after cold must be warm unless one repair occurs")
    attempt_ids, prepare_attempt_ids, call_ids = set(), set(), set()
    owner_ids, artifact_ids, verifier_ids = set(), set(), set()
    digest_by_task = {}
    for index, row in enumerate(rows):
        if type(row) is not dict or set(row) != {
                "task_id", "mode", "source_task_id", "plan_sha256",
                "raw_generation", "prepare_receipt", "execution"}:
            _fail("plan evidence row fields are invalid")
        mode = row["mode"]
        source = row["source_task_id"]
        raw = row["raw_generation"]
        prepared = row["prepare_receipt"]
        execution = row["execution"]
        if type(raw) is not dict or type(prepared) is not dict or type(execution) is not dict:
            _fail("generation, prepare and execution receipts are required")

        if mode in {"cold", "repair"}:
            if source is not None:
                _fail("generated plans cannot cite a source task")
            if set(raw) != {"attempt_id", "provider_status", "plan"}:
                _fail("generated plan must link one completed provider attempt and raw plan")
            attempt = raw["attempt_id"]
            if (type(attempt) is not str or not attempt or attempt in attempt_ids
                    or raw["provider_status"] != "completed"):
                _fail("plan generation attempt is missing, duplicated or incomplete")
            attempt_ids.add(attempt)
            digest = canonical_plan_sha256(raw["plan"])
            if row["plan_sha256"] != digest:
                _fail("plan digest does not match retained provider plan")
        else:
            if raw != {"provider_generation_count": 0}:
                _fail("warm reuse must explicitly show no provider generation")
            if type(source) is not str or source not in digest_by_task:
                _fail("warm task source must be an earlier generated-plan task")
            digest = digest_by_task[source]
            if row["plan_sha256"] != digest:
                _fail("warm plan digest differs from its source task")

        prepare_required = {"call_id", "attempt_id", "status", "submitted_plan",
                            "task_plan_sha256", "artifact_id", "owner_id"}
        if set(prepared) != prepare_required or prepared["status"] != "prepared":
            _fail("public prepare receipt is incomplete")
        if prepared["submitted_plan"] is None or canonical_plan_sha256(
                prepared["submitted_plan"]) != digest:
            _fail("submitted public prepare plan differs from provider lineage")
        if prepared["task_plan_sha256"] != digest:
            _fail("parent-retained artifact digest differs from provider plan")
        if type(prepared["call_id"]) is not str or not prepared["call_id"] or prepared["call_id"] in call_ids:
            _fail("public prepare call is missing or duplicated")
        call_ids.add(prepared["call_id"])
        if type(prepared["attempt_id"]) is not str or not prepared["attempt_id"]:
            _fail("public prepare attempt ID is required")
        prepare_attempt = prepared["attempt_id"]
        if prepare_attempt in prepare_attempt_ids:
            _fail("every public prepare call requires a fresh attempt ID")
        prepare_attempt_ids.add(prepare_attempt)
        artifact = prepared["artifact_id"]
        if type(artifact) is not str or not artifact or artifact in artifact_ids:
            _fail("every task requires a fresh parent artifact identity")
        artifact_ids.add(artifact)
        owner = prepared["owner_id"]
        if type(owner) is not str or not owner or owner in owner_ids:
            _fail("every task requires a fresh owner identity")
        owner_ids.add(owner)

        exec_required = {"call_id", "task_plan_sha256", "outcome",
                         "release_confirmed", "task_success", "verifier_id",
                         "independent_score"}
        if set(execution) != exec_required:
            _fail("compiled execution and post-close score receipt are required")
        if (execution["call_id"] != prepared["call_id"]
                or execution["task_plan_sha256"] != digest):
            _fail("compiled result is not bound to the prepared call and plan")
        if (execution["outcome"] != "SAFE_YIELD"
                or execution["release_confirmed"] is not True
                or execution["task_success"] is not True
                or execution["independent_score"] is not True):
            _fail("task effect, release and independent post-close score must pass")
        verifier = execution["verifier_id"]
        if (type(verifier) is not str or not verifier or verifier in verifier_ids):
            _fail("each task requires a fresh post-close verifier identity")
        verifier_ids.add(verifier)
        digest_by_task[row["task_id"]] = digest

        if mode == "cold":
            if prepared["attempt_id"] != raw["attempt_id"]:
                _fail("cold prepare attempt does not join its provider generation")
        elif mode == "repair":
            if prepared["attempt_id"] != raw["attempt_id"]:
                _fail("repair prepare attempt does not join its provider generation")
            if digest == digest_by_task[rows[0]["task_id"]]:
                _fail("repair must generate a different semantic plan")
        else:
            if prepared["attempt_id"] in attempt_ids:
                _fail("warm reuse must have its own task attempt identity")
            if prepared["attempt_id"] == raw.get("attempt_id"):
                _fail("warm reuse cannot reuse the source generation attempt")

    for index, mode in enumerate(modes[1:], start=1):
        expected_source = (rows[0]["task_id"] if mode == "warm" else
                           rows[repair_positions[0]]["task_id"]
                           if mode == "post_repair_warm" else None)
        if mode == "repair" and rows[index]["task_id"] == rows[0]["task_id"]:
            _fail("repair task needs fresh task identity")
        if mode != "repair" and rows[index]["source_task_id"] != expected_source:
            _fail("reuse row must cite its source generation task")
        if mode == "repair" and rows[index]["source_task_id"] is not None:
            _fail("repair generation must not claim a reuse source")
    return {"task_count": len(rows), "generated_plan_count": len(attempt_ids),
            "provider_generation_attempt_ids": sorted(attempt_ids),
            "validated_task_ids": list(by_task)}
