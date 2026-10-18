#!/usr/bin/env python3
"""Independent raw/source gate for the V15 dropped-KeyRelease probe."""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path("/src")
PACKAGE = ROOT / "research/doom/map01_v39_v15_keyup_loss_a01_20261005"
freeze = json.loads((PACKAGE / "FREEZE.json").read_text(encoding="utf-8"))
raw_path = pathlib.Path(sys.argv[1])
raw = json.loads(raw_path.read_text(encoding="utf-8"))
checks = []


def check(name, condition, detail):
    checks.append({"name": name, "pass": bool(condition), "detail": detail})


check("raw_schema", raw.get("schema") == "v39-v15-keyup-loss-a01-raw-v1",
      str(raw.get("schema")))
check("raw_base", raw.get("source_base") == freeze.get("base_commit"),
      str(raw.get("source_base")))
check("claims_false", all(value is False for value in raw.get("claims", {}).values()),
      json.dumps(raw.get("claims", {}), sort_keys=True))
cases = raw.get("cases", [])
check("two_cases", len(cases) == 2,
      f"count={len(cases)}")
by_loss = {case.get("injected_keyrelease_loss"): case for case in cases}
check("normal_case_present", False in by_loss, "expected injected loss false")
check("loss_case_present", True in by_loss, "expected injected loss true")

normal = by_loss.get(False, {})
normal_row = normal.get("release_row") or {}
check("normal_server_empty", normal.get("server_keycodes_down_after_batch") == [],
      json.dumps(normal.get("server_keycodes_down_after_batch")))
check("normal_batch_verified", normal_row.get("owner_transition_verified") is True,
      str(normal_row.get("owner_transition_verified")))
check("normal_terminal_clean", normal.get("terminal_cleanup_recovered") is True
      and normal.get("terminal_close_error") is None,
      f"recovered={normal.get('terminal_cleanup_recovered')} error={normal.get('terminal_close_error')}")

lost = by_loss.get(True, {})
lost_row = lost.get("release_row") or {}
lost_server_down = lost.get("server_keycodes_down_after_batch")
check("loss_exposes_key_down", lost_server_down == [38], str(lost_server_down))
check("loss_batch_does_not_claim_physical", lost_row.get("physical_verification_authoritative") is False,
      str(lost_row.get("physical_verification_authoritative")))
check("loss_batch_owner_verified", lost_row.get("owner_transition_verified") is True,
      str(lost_row.get("owner_transition_verified")))
check("loss_terminal_diagnostic", bool(lost.get("terminal_close_error"))
      and any(row.get("verified") is False and row.get("keys_down") == [38]
              for row in lost.get("terminal_owner_release_rows", [])),
      f"error={lost.get('terminal_close_error')} records={len(lost.get('terminal_owner_release_rows', []))}")
check("loss_not_recovered", lost.get("terminal_cleanup_recovered") is False,
      str(lost.get("terminal_cleanup_recovered")))

source_hashes = {}
for rel, expected in freeze["source_sha256"].items():
    path = ROOT / rel
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    source_hashes[rel] = {"expected": expected, "actual": actual, "pass": actual == expected}
check("production_sources_match_freeze", all(x["pass"] for x in source_hashes.values()),
      json.dumps(source_hashes, sort_keys=True))
candidate_path = PACKAGE / "candidate.py"
candidate_hash = hashlib.sha256(candidate_path.read_bytes()).hexdigest()
check("candidate_matches_freeze", candidate_hash == freeze["candidate_sha256"],
      candidate_hash)

passed = all(item["pass"] for item in checks)
out = {"schema": "v39-v15-keyup-loss-a01-audit-v1",
       "status": "PASS_RAW_AND_SOURCE_AUDIT" if passed else "FAIL_RAW_OR_SOURCE_AUDIT",
       "decision": ("FAIL_BATCH_PHYSICAL_RELEASE_NOT_ESTABLISHED" if passed and
                    lost_row.get("owner_transition_verified") is True and lost_server_down
                    else "PASS_FAIL_CLOSED" if passed else "AUDIT_FAILURE"),
       "raw_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
       "checks": checks}
pathlib.Path("/out/audit.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n",
                                            encoding="utf-8")
print(json.dumps({"status": out["status"], "decision": out["decision"],
                  "passed": sum(item["pass"] for item in checks), "checks": len(checks)}))
