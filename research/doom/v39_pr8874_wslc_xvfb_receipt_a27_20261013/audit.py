from pathlib import Path
import hashlib, importlib.util, json
ROOT=Path(__file__).resolve().parent; rawp=ROOT/'results/a27-01/raw.json'; raw=json.loads(rawp.read_text()); manifest=json.loads((ROOT/'SOURCE_MANIFEST.json').read_text())
sources=[]
for x in manifest['files']:
 b=(ROOT/'INPUT'/x['path']).read_bytes(); h=hashlib.sha256(b).hexdigest(); sources.append({'path':x['path'],'ok':h==x['sha256'] and len(b)==x['bytes'],'sha256':h})
spec=importlib.util.spec_from_file_location('a27_analyzer',ROOT/'INPUT/research/doom/analyze_map01_direct_retained_input_v2.py'); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
recomputed=module.analyze(raw['events']); releases=[r for r in raw['owner_cleanup']['records'] if r.get('event')=='owner_release' and r.get('reason')=='cancelled']
release=releases[0] if len(releases)==1 else {}; attempts=release.get('key_release_attempts',{}).get(str(raw['keycode']),{}) if release else {}
expected_pending=[{'backend_owned_before_release':True,'disposition':'not_attempted_owner_cancel_release','identifier':'a27-probe','key':'w','step':0}]
checks={
 'keypress_then_same_key_release_same_window':len(raw['client_events'])==2 and [e['type'] for e in raw['client_events']]==[2,3] and all(e['detail']==raw['keycode'] and e['window']==raw['window'] for e in raw['client_events']),
 'independent_keymap_down_then_up':raw['keymap']=={'after_cancel_release':False,'while_held':True},
 'observed_recovery_within_preregistered_two_seconds':type(raw.get('recovery_latency_ns')) is int and 0<=raw['recovery_latency_ns']<=2_000_000_000,
 'owner_cancel_receipt_verified_empty':len(releases)==1 and release.get('verified') is True and release.get('keys_down')==[] and release.get('buttons_down')==[] and release.get('keys_unknown')==[] and attempts.get('verified') is True and len(attempts.get('attempts',[]))==1 and attempts['attempts'][0].get('server_key_down_before') is True and attempts['attempts'][0].get('server_key_down_after') is False,
 'queued_up_not_attempted_and_not_replayed':raw['terminal_release'].get('cancelled_pending_ups')==expected_pending and not any(r.get('event')=='owner_explicit_keyup' for r in raw['owner_cleanup']['records']),
 'terminal_release_empty_and_cache_cleared':raw['terminal_release'].get('verified') is True and raw['terminal_release'].get('keys_down')==[] and raw.get('admission_cache_entries_after_terminal')==0,
 'owner_stopped_and_xvfb_clean':raw['owner_cleanup']['closed'] and raw['owner_cleanup']['stopped'] and not raw['owner_cleanup']['thread_alive'] and raw['xvfb_exit']==0,
 'candidate_exit_and_container_removed':(ROOT/'results/a27-01/container.exit').read_text().strip()=='0' and len((ROOT/'results/a27-01/container-inventory-after.txt').read_text(encoding='utf-8-sig').splitlines())<=2,
 'frozen_sources_match':bool(sources) and all(x['ok'] for x in sources),
 'analyzer_did_not_claim_up_measurement':raw.get('analyzer')==recomputed and recomputed.get('measurement_ready') is False and recomputed.get('unmatched_admission_count')==1 and not any(e.get('event')=='input_release_transition' for e in raw['events']),
}
result={'experiment_id':'v39_pr8874_wslc_xvfb_receipt_a27_20261013','decision':'PASS_METHOD_SCOPED' if all(checks.values()) else 'FAIL_AUDIT','checks':checks,'source_checks':sources,'raw_sha256':hashlib.sha256(rawp.read_bytes()).hexdigest(),'cancel_to_keyrelease_ms':raw['recovery_latency_ns']/1e6,'cancel_to_owner_verified_ms':(release['verified_ns']-raw['cancel_requested_ns'])/1e6 if release else None,'analyzer_recomputed':recomputed,'scope':'One virtual X11 key cancellation recovery. It establishes bounded X-server release and owner cleanup only; no explicit-UP retention measurement, application response, model, live threat, or task effect.'}
(ROOT/'results/a27-01/audit.json').write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps({'decision':result['decision'],'failed_checks':[k for k,v in checks.items() if not v],'cancel_to_keyrelease_ms':result['cancel_to_keyrelease_ms'],'cancel_to_owner_verified_ms':result['cancel_to_owner_verified_ms']},indent=2))
