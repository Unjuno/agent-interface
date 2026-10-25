"""Classify A14 recovery without the known A13 naive-cancel false negative."""
from pathlib import Path
import json
from audit_recovery_censoring import analyze
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
ALLOC="map01-v39-live-threat-guard-a14-recovery-20261009"
ROOT=REPO/"results-local/doom"/ALLOC
PROVENANCE=("allocation_identity","source_commit_is_verified_prelaunch_main","runtime_source_closure_is_complete_and_frozen","all_runtime_sources_match_local_and_frozen_main","guest_host_source_mapping_is_frozen","known_startup_dependencies_are_frozen","no_preexisting_game_or_display_process","runner_and_auditor_hashes_match_freeze","fixture_hashes_match_freeze","qualified_wad_hash_matches","forwarded_images_host_receipts_valid")
SAFETY=("all_accepted_programs_have_terminals","per_key_release_rows_accounted","terminal_releases_verified_empty","no_stale_admission_after_guard")
def main():
 freeze=json.loads((ROOT/"FREEZE.json").read_text());audit=json.loads((ROOT/"AUDIT.json").read_text());custody=json.loads((ROOT/"A14_CUSTODY_INDEPENDENT.json").read_text());report=json.loads((ROOT/"episode/report.json").read_text())
 censor=analyze(report.get("decisions",[]),freeze["runtime"]["iterations"])
 (ROOT/"A14_RECOVERY_CENSORING.json").write_text(json.dumps({"schema":"map01-v39-live-threat-guard-a14-recovery-censoring-v1","allocation":ALLOC,**censor},indent=2)+"\n")
 checks=audit.get("checks",{});provenance=all(checks.get(k) is True for k in PROVENANCE);safety=all(checks.get(k) is True for k in SAFETY);custody_ok=custody.get("custody_pass") is True
 counts=censor["classifications"];recovered=counts["recovered_within_two_decisions"];missed=counts["observable_recovery_missed"]
 if not provenance or not safety or not custody_ok: status="FAIL"
 elif audit.get("controller_failure") is not None: status="STOP"
 elif recovered>0 and missed==0: status="PASS"
 else: status="HOLD"
 result={"schema":"map01-v39-live-threat-guard-a14-recovery-result-v1","allocation":ALLOC,"status":status,"initial_audit_status_preserved":audit.get("status"),"initial_naive_cancel_check_preserved":checks.get("cancelled_cover_has_matching_release_event"),"provenance_checks_passed":provenance,"input_safety_checks_passed":safety,"independent_cancellation_custody_passed":custody_ok,"recovery_classifications":counts,"scope":"One descriptive live recovery observation. PASS applies only to observing a fresh recovery within two decisions after at least one hard-health guard with no fully observed miss; it does not close Issue #59 or establish useful feedback, causal benefit, MAP01 completion, physical key state, or game consumption."}
 (ROOT/"A14_RESULT.json").write_text(json.dumps(result,indent=2)+"\n");print(json.dumps(result,indent=2));return 0 if status in ("PASS","HOLD") else 1
if __name__=="__main__": raise SystemExit(main())
