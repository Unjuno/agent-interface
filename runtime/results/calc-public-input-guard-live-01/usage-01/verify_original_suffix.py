"""Match original bytes or approved context projections at retained byte offsets."""
import json
from pathlib import Path
from context_projection import original_matches
ROOT=Path(__file__).resolve().parent
SOURCE=Path('/mnt/c/Users/junny/.codex/sessions/2026/09/12/rollout-2026-09-12T23-46-37-01a09615-a96c-7b70-8284-e6391b885be5.jsonl')
def verify():
 records=[json.loads(line) for line in (ROOT/'primary-source-records.jsonl').read_text().splitlines()]
 boundary=json.loads((ROOT/'original-suffix-verification.json').read_text())
 begin,end=boundary['source_byte_begin'],boundary['source_byte_end']
 with SOURCE.open('rb') as stream:
  stream.seek(begin);data=stream.read(end-begin)
 lines=data.decode().splitlines(keepends=True);first=records[0]['source_line']
 for record in records:
  offset=record['source_line']-first
  if offset<0 or offset>=len(lines) or not original_matches(record,lines[offset]):
   raise ValueError('original record or approved context projection mismatch')
 return {'status':'PASS_ORIGINAL_RANGE_AND_PUBLIC_PROJECTION','retained_records_matched':len(records),'projected_contexts':sum('privacy_projection' in r for r in records),'relative_source_line_positions_exact':True,'original_byte_range':[begin,end],'bytes_read':len(data),'absolute_line_labels':'collector full sequential scan; historical prefix not independently recounted','scope':'exact non-context records; original hashes and approved model/turn/effort projection for context records; not billing or immutable model attestation'}
if __name__=='__main__':
 result=verify();text=json.dumps(result,indent=2);(ROOT/'public-projection-original-verification.json').write_text(text+'\n');print(text)
