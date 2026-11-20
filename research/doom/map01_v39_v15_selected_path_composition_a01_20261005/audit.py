import hashlib, json, sys
from pathlib import Path

root = Path(__file__).resolve().parent
errors = []
def check(name, condition, detail):
    if not condition:
        errors.append({"check": name, "detail": detail})

raw_path = root / "run" / "candidate.stdout"
exit_text = (root / "run" / "candidate.exit").read_text(encoding="utf-8").strip()
stderr = (root / "run" / "candidate.stderr").read_bytes()
raw = raw_path.read_bytes()
d = json.loads(raw.decode("utf-8"))
route = d["route"]
trace = d["trace"]
checks = []
check("candidate_exit_zero", exit_text == "0", exit_text)
check("stderr_empty", len(stderr) == 0, f"stderr_bytes={len(stderr)}")
check("selected_v15", route.get("selected_session") == "session_map01_v15.py" and route.get("selected_is_v15") is True, str(route.get("selected_session")))
check("release_batch_backend_v1", route.get("backend_is_release_batch_v1") is True and route.get("installed_backend") == "doom_owner_thread_release_batch_backend_v1.Backend", str(route.get("installed_backend")))
check("executor_v13", route.get("executor_is_v13") is True and route.get("installed_executor") == "executor_v13.Executor", str(route.get("installed_executor")))
rows = route.get("release_rows", [])
check("exact_release_rows", [r.get("key") for r in rows] == ["space", "F8"], str([r.get("key") for r in rows]))
owner_ids = set()
for row, key, code in zip(rows, ["space", "F8"], [65, 74]):
    receipt = row.get("owner_thread_keyup_receipt") or {}
    check(f"{key}_receipt_identity", receipt.get("event") == "owner_explicit_keyup" and receipt.get("operation") == "up" and receipt.get("key") == key and receipt.get("keycode") == code and receipt.get("server_sync_completed") is True and receipt.get("physical_verification_authoritative") is False, json.dumps(receipt, sort_keys=True))
    check(f"{key}_row_receipt_binding", row.get("owner_thread_keyup_receipt_count") == 1 and row.get("owner_thread_keyup_verified") is True and row.get("owner_transition_verified") is True and row.get("owner_id") == receipt.get("owner_id") and row.get("intent_token") == receipt.get("intent_token"), json.dumps({k: row.get(k) for k in ["owner_id", "intent_token", "owner_thread_keyup_receipt_count", "owner_thread_keyup_verified", "owner_transition_verified"]}, sort_keys=True))
    owner_ids.add(receipt.get("owner_id"))
check("same_owner", len(owner_ids) == 1 and None not in owner_ids, str(owner_ids))
ups = [i for i, e in enumerate(trace) if e.get("kind") == "xtest_key_up"]
keymaps = [i for i, e in enumerate(trace) if e.get("kind") == "query_keymap"]
check("two_explicit_up_events", len(ups) == 2, str(ups))
inter_up_queries = [i for i in keymaps if len(ups) == 2 and ups[0] < i < ups[1]]
check("no_keymap_query_between_ups", len(inter_up_queries) == 0, str(inter_up_queries))
post_sample = [i for i, e in enumerate(trace) if e.get("kind") == "post_batch_sampler_result"]
telemetry = [i for i, e in enumerate(trace) if e.get("kind") == "telemetry_emit" and e.get("event") == "input_release_transition"]
owner_state_after = [i for i, e in enumerate(trace) if e.get("kind") in ("owner_query_focus", "owner_query_pointer") and len(ups) == 2 and i > ups[-1]]
check("sample_after_up_and_owner_state", len(post_sample) == 1 and len(owner_state_after) > 0 and ups[-1] < max(owner_state_after) < post_sample[0], str({"last_up": ups[-1] if ups else None, "owner_state": owner_state_after, "sample": post_sample}))
check("sampler_query_precedes_sample", len(keymaps) >= 1 and len(post_sample) == 1 and keymaps[0] < post_sample[0], str({"keymaps": keymaps, "sample": post_sample}))
check("sample_before_release_telemetry", len(post_sample) == 1 and len(telemetry) == 2 and post_sample[0] < min(telemetry), str({"sample": post_sample, "telemetry": telemetry}))
check("sample_rows_downgraded", d.get("sample", {}).get("status") == "SAMPLED" and d["sample"].get("keycodes_down") == [] and all(r.get("post_batch_keymap_status") == "SAMPLED" and r.get("post_batch_key_down") is False and r.get("post_batch_keycodes_down") == [] for r in rows), json.dumps(d.get("sample"), sort_keys=True))
check("final_server_keys_empty", route.get("post_close_server_keys") == [] and d.get("final_server_keycodes_down") == [], str({"post_close": route.get("post_close_server_keys"), "final": d.get("final_server_keycodes_down")}))
check("no_authority_or_physical_claim", route.get("authority_claims", {}).get("grants_input_authority") is False and route.get("authority_claims", {}).get("physical_verification_authoritative") is False and d.get("claims", {}).get("real_input") is False and d.get("claims", {}).get("real_x11") is False and d.get("claims", {}).get("application") is False and d.get("claims", {}).get("physical_keyboard") is False, json.dumps({"claims": d.get("claims"), "authority": route.get("authority_claims")}, sort_keys=True))
freeze = json.loads((root / "PRE-RUN.json").read_text(encoding="utf-8"))
check("protocol_preserves_scope_limits", freeze.get("boundaries", {}).get("not_exercised") is not None and freeze.get("boundaries", {}).get("stubbed") is not None and freeze.get("candidate_invocations") == 1 and freeze.get("retries") == 0, json.dumps(freeze.get("boundaries"), sort_keys=True))
result = {
  "schema": "v39-v15-selected-path-composition-a01-audit-v1",
  "status": "PASS_SOURCE_COMPOSITION_ONLY" if not errors else "FAIL",
  "raw_stdout_sha256": hashlib.sha256(raw).hexdigest(),
  "raw_stderr_sha256": hashlib.sha256(stderr).hexdigest(),
  "candidate_exit": exit_text,
  "candidate_invocations": 1,
  "auditor_invocations": 1,
  "retries": 0,
  "checks_passed": 17 - len(errors),
  "checks_total": 17,
  "errors": errors,
  "scope": "Frozen synthetic source-composition qualification only. V39 session_command selector and actual V15 wrapper/release-batch/owner/V13 class body were bound; controller/game/Xlib and typed backend parent boundaries were stubbed. No full startup, real X11, physical key state, application effect, threat response, latency, feedback usefulness, recovery efficacy, or gameplay claim. XSync receipt establishes server synchronization only."
}
(root / "AUDIT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, sort_keys=True))
sys.exit(0 if not errors else 1)
