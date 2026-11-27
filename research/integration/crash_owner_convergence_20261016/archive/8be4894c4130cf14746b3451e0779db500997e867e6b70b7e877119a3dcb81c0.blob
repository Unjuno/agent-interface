#!/usr/bin/env python3
"""Source-only topology audit; no session, game, or GUI is launched."""
import ast,hashlib,json,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parents[4]
PKG=ROOT/'research/doom/v39_crash_recovery_integration_audit_20261012'
f=json.loads((PKG/'FREEZE.json').read_text()); src={p:(ROOT/p).read_text(encoding='utf8') for p in f['sources_sha256']}
controller=src['research/doom/map01_overlap_controller_v39.py']; session=src['research/doom/session_map01_v12.py']; measured=src['research/doom/session_map01_v15.py']; backend=src['research/doom/doom_owner_thread_release_batch_backend_v1.py']; typed=src['research/doom/doom_typed_release_backend_v2.py']; cleanup=src['research/doom/doom_controller_failure_cleanup_v1.py']; owner=src['research/live_control/input_owner_v12.py']; executor=src['research/live_control/executor_v12.py']
checks={
 'all_pinned_sources_match':all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in f['sources_sha256'].items()),
 'controller_launches_session_as_subprocess':'subprocess.Popen(session_command(args, runtime)' in controller and 'failure_cleanup.track(process)' in controller,
 'default_v12_and_optin_v15_sessions_share_child_boundary':'session_map01_v15.py' in controller and 'session_map01_v12.py' in controller,
 'session_constructs_backend_and_executor_in_same_process':'backend = Backend(session, args.out, emit, signal_readers)' in session and 'executor = Executor(backend, emit)' in session,
 'v15_patches_v12_backend_and_executor_in_child':'base.Backend=TelemetryBackend' in measured and 'base.Executor=ReleaseOrderedExecutor' in measured and 'base.main()' in measured,
 'production_backend_constructs_inputowner_from_session_display':'InputOwner(session.name)' in backend and 'InputOwner(session.name)' in typed,
 'inputowner_is_thread_inside_host_process':'threading.Thread(target=self._thread_main, name=\'input-owner\', daemon=True)' in owner,
 'executor_worker_is_thread_inside_host_process':bool(re.search(r'threading\.Thread\([\s\S]{0,120}target=self\._run',executor)),
 'ready_protocol_does_not_publish_display_name':bool(re.search(r'emit\(\s*\{\s*"event":\s*"ready"',session)) and '"display": session.name' not in session,
 'parent_failure_cleanup_can_terminate_or_kill_only_tracked_child':'child.terminate' in cleanup and 'child.kill' in cleanup,
 'parent_cleanup_has_no_inputowner_release_client':'input_transition_owner_v4' not in cleanup and 'InputOwner(' not in cleanup and 'Xlib' not in cleanup,
}
lines={p:{'sha256':h} for p,h in f['sources_sha256'].items()}
out={'schema':'v39-crash-recovery-current-topology-audit-v1','decision':'PASS_SOURCE_GRAPH' if all(checks.values()) else 'STOP','evidence_kind':'static source inspection; not runtime behavior','checks':checks,'pinned_sources':lines,'integration_judgment':{'current_failure_domain':'The MAP01 session subprocess creates the Executor and owner-thread InputOwner. A hard death of that subprocess removes both; the outer controller only knows the child process and has no display-bound release client.','recovery_direction':'Move input ownership into a longer-lived supervisor/service outside the session/Executor child failure domain. Add a strict local RPC adapter in the session backend, publish the display/auth context before input authority, and on child EOF close the owner and persist verified release evidence before any new admission.','boundary':'A supervisor-service death still needs an external restart/display-reset policy; A04 proves only Executor-child death while the owner supervisor remains alive.'}}
(PKG/'results/source_audit.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,sort_keys=True)); raise SystemExit(not all(checks.values()))
