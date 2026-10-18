#!/usr/bin/env python3
import json,sys
from pathlib import Path
raw=json.loads(Path(sys.argv[1]).read_text())
assert raw['main_sha']=='6a2826d391b77496b69752609a6f07b6971b4b6f'
assert raw['source_git_blob']=='e701035302da4802e0db463035c4d653a7e7618b'
assert raw['source_sha256']=='97d60f64ae6dc075fd7b18a452813c90d7c5d366d71e324905c17d74604585b2'
expected={
 'baseline':({'events.jsonl':1,'delivered.jsonl':1},{'events.jsonl':1,'delivered.jsonl':1}),
 'before_first_append':({'events.jsonl':0,'delivered.jsonl':0},{'events.jsonl':1,'delivered.jsonl':1}),
 'after_first_append':({'events.jsonl':1,'delivered.jsonl':0},{'events.jsonl':2,'delivered.jsonl':1}),
 'after_second_append':({'events.jsonl':1,'delivered.jsonl':1},{'events.jsonl':2,'delivered.jsonl':2}),}
assert len(raw['cases'])==4
for row in raw['cases']:
 b,a=expected[row['name']]
 for key,n in b.items(): assert row['before_retry'][key]['rows']==n,(row,key,'before',row['before_retry'])
 for key,n in a.items():
  got=row['after_retry'][key]
  assert got['rows']==n,(row,key,'after',got)
  assert got['release_ids']==['probe-release-001']*n,(row,key,got)
 assert (row['first_error'] is None)==(row['name']=='baseline'),row
assert raw['executor_policy_source_review']['attempt_recorded_before_emit'] is True
assert raw['executor_policy_source_review']['automatic_retry'] is False
print(json.dumps({'audit':'PASS_SCOPED_PREFIX_AND_RETRY_DUPLICATION','cases':len(raw['cases']),
 'between_file_retry_duplicates_events':True,'stdout_retry_duplicates_both':True,
 'executor_policy':'DELIVERY_UNKNOWN_NO_AUTOMATIC_RETRY'},sort_keys=True))
