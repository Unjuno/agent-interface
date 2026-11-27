from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RUN = ROOT / "run"
SERVER = RUN / "server"


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def audit():
    result = read(RUN / "RESULT.json")
    ledger = read(RUN / "LEDGER-RECONCILED.json")
    selected = read(RUN / "model-selected-point.json")
    invalidation = read(RUN / "generation-invalidation-marker.json")
    generations = read(RUN / "generation-observations.json")
    owner_events = read(RUN / "owner-input-events.json")
    close_files = list(SERVER.glob("session-*-close.json"))
    close = read(close_files[0]) if len(close_files) == 1 else {}
    prelaunch = read(ROOT / "PRELAUNCH.json")
    conditions = read(ROOT / "CONDITIONS.json")
    checks = {
        "one_completed_real_model_turn": result.get("provider_status") == "completed" and
            result.get("provider_usage", {}).get("status") == "reported",
        "model_saw_exact_public_image": result.get("model_image_sha256") ==
            result.get("observation_image_sha256"),
        "model_point_inside_green_target": result.get("selected_point_inside_green") is True,
        "generation_invalidated_after_provider_before_mint":
            invalidation.get("written_after_provider_response") is True and
            invalidation.get("written_before_public_mint") is True and
            result.get("process_generation") == "a" * 64 and
            any(row.get("sequence", 0) > result.get("observation_sequence", 0) and
                row.get("process_generation") == "b" * 64 for row in generations),
        "mint_uses_original_observation_sequence":
            result.get("mint_status") == "minted" and
            result.get("mint_source_sequence") == result.get("observation_sequence") ==
            result.get("mint_created_sequence"),
        "standard_compiled_caller_refused_stale_generation":
            result.get("runtime_outcome") == "SAFE_YIELD" and
            result.get("refusal_reason") == "association_changed" and
            result.get("completed_transitions") == 0 and
            len(result.get("admission_refusals", [])) == 1 and
            result["admission_refusals"][0].get("status") == "association_changed",
        "no_owner_input_or_application_effect": not owner_events and
            result.get("owner_click_count") == 0 and
            result.get("effect_receipt_count") == 0 and
            result.get("application_state_unchanged") is True and
            not list(SERVER.rglob("synthetic-target-click.json")) and
            not list(SERVER.rglob("synthetic-effect-receipt.json")),
        "neutral_session_close_verified": len(close_files) == 1 and
            close.get("verified") is True and close.get("release_confirmed") is True,
        "runtime_task_success_remains_null": result.get("runtime_task_success") is None,
        "ledger_complete_and_score_matches_refusal_oracle": ledger.get("complete") is True and
            any(event.get("kind") == "task_score" and event.get("task_success") is True
                for event in ledger.get("events", [])),
        "no_wslc_docker_or_physical_input": conditions.get("wslc_used") is False and
            conditions.get("docker_used") is False and conditions.get("physical_input") is False,
        "prelaunch_sources_match": prelaunch.get("classification") == "FROZEN_BEFORE_PROVIDER_CALL" and
            all(hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == digest
                for rel, digest in prelaunch.get("source_sha256", {}).items()),
    }
    manifest = []
    for line in (RUN / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, rel = line.split("  ", 1)
        manifest.append(hashlib.sha256((RUN / rel).read_bytes()).hexdigest() == digest)
    checks["raw_manifest_all_match"] = bool(manifest) and all(manifest)
    redactions = read(ROOT / "REDACTIONS.json").get("redactions", [])
    checks["redaction_hashes_match"] = bool(redactions) and all(
        row.get("redacted_sha256") == hashlib.sha256(
            (ROOT / row["path"]).read_bytes()).hexdigest() for row in redactions)
    report = {
        "schema": "agent-interface/appserver-p08-stale-generation-audit-v1",
        "classification": "PASS_SCOPED" if all(checks.values()) else "FAIL_OR_HOLD",
        "checks": checks,
        "scope": "one real model wait, standard public compiled MCP, synthetic Fake X process-generation refusal",
        "physical_input": False,
        "wslc_used": False,
        "matched_efficiency_or_reliability": False,
    }
    (ROOT / "AUDIT.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                                      encoding="utf-8", newline="\n")
    return report


if __name__ == "__main__":
    output = audit()
    print(json.dumps(output, indent=2, sort_keys=True))
    raise SystemExit(0 if output["classification"] == "PASS_SCOPED" else 1)
