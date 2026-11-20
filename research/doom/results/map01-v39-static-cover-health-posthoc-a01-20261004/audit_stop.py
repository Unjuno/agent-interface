import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent
raw=Path('research/doom/results/map01-v39-coast-liveness-live-01/runtime/events.jsonl')
run=json.loads((root/'RUN.json').read_text(encoding='utf-8-sig'))
candidate=json.loads((root/'CANDIDATE_RESULT.json').read_text(encoding='utf-8'))
primary=json.loads((root/'PRIMARY_AUDIT.json').read_text(encoding='utf-8'))
stop=json.loads((root/'STOP_AUDIT.json').read_text(encoding='utf-8'))
freeze=(root/'FREEZE.md').read_text(encoding='utf-8-sig')
checks={
 'retained_stop_before_mutation_control':run.get('result')=='STOP' and run.get('exit_code')==2 and 'NEGATIVE_CONTROL_REJECTED' not in (root/'RAW_TEST.txt').read_text(encoding='utf-8-sig'),
 'primary_candidate_result_was_checked':primary.get('pass') is True and candidate.get('cover_samples',{}).get('last',{}).get('health')==48,
 'runner_syntax_failure_exactly_recorded':'Syntax error: end of file unexpected (expecting "fi")' in (root/'RAW_TEST.txt').read_text(encoding='utf-8-sig'),
 'raw_source_identity_frozen':hashlib.sha256(raw.read_bytes()).hexdigest()==candidate.get('source_events_sha256') and candidate.get('source_events_sha256') in freeze,
 'stop_audit_pass':stop.get('pass') is True and all(stop.get('checks',{}).values()),
}
out={'schema':'v39-static-cover-health-posthoc-package-stop-audit-a01-v1','pass':all(checks.values()),'checks':checks}
(root/'PACKAGE_STOP_AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps(out,indent=2,sort_keys=True))
raise SystemExit(0 if out['pass'] else 1)
