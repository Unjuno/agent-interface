from pathlib import Path
import hashlib, json
p=Path(__file__).resolve().parent
result=json.loads((p/'RESULT.json').read_text(encoding='utf-8-sig'))
exact=json.loads((p/'raw-exact-closure-01.txt').read_text(encoding='utf-8-sig'))
raw=(p/'raw-run-01.txt').read_text(encoding='utf-8-sig')
negative=(p/'raw-negative-control-01.txt').read_text(encoding='utf-8-sig')
manifest={}
for line in (p/'ARTIFACT_SHA256SUMS').read_text(encoding='ascii').splitlines():
    digest,name=line.split('  ',1); manifest[name]=digest
manifest_valid=all(hashlib.sha256((p/name).read_bytes()).hexdigest()==digest for name,digest in manifest.items())
checks={
  'result_schema': result['schema']=='issue59-release-order-result-v1',
  'wrapper_control_pass': '"all": true' in raw and '"no_input_state_between_keyups": true' in raw,
  'wrapper_negative_detected': '"no_input_state_between_keyups": false' in negative,
  'exact_closure_baseline_pass': exact['baseline']['all'] is True,
  'exact_closure_negative_detected': exact['negative_control']['all'] is False,
  'exact_closure_no_keymap_in_batch': not any(e['event']=='query_keymap' for e in exact['baseline']['trial_events']),
  'cleanup_keymap_outside_batch': any(e['event']=='query_keymap' for e in exact['baseline']['post_trial_cleanup_events']),
  'source_manifest_present': (p/'SOURCE_SHA256SUMS').is_file(),
  'artifact_manifest_valid': manifest_valid,
}
assert all(checks.values()), checks
print(json.dumps({'audit':'PASS','checks':checks,'verified_artifact_sha256':manifest},sort_keys=True,indent=2))

