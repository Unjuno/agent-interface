#!/usr/bin/env python3
import argparse,json,hashlib
from pathlib import Path
from logic import classify_candidate

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--matrix',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();agg=json.loads((a.matrix/'aggregate.json').read_text());rows=[r for b in agg['blocks'] for r in b['report']['rows']];counts={}
 for r in rows:counts[r['condition']]=counts.get(r['condition'],0)+1
 candidate=[r for r in rows if r['condition'] not in ('baseline_gap','stale_uid')]
 unsafe=[r for r in candidate if classify_candidate(int(r['count']),r['final'])=='UNSAFE_OR_UNEXPECTED']
 lost=[r for r in rows if r['condition']=='baseline_gap' and r['final']=='bookkeeperoffice']
 stale=[r for r in rows if r['condition']=='stale_uid' and r['refused'] and r['final']=='book']
 report={'rows':len(rows),'counts':counts,'baseline_lost_update':len(lost),'candidate_trials':len(candidate),'candidate_unsafe':len(unsafe),'stale_uid_refusals':len(stale),'passed':len(rows)==28 and len(lost)==4 and len(candidate)==20 and len(unsafe)==0 and len(stale)==4 and agg['passed'],'aggregate_sha256':hashlib.sha256((a.matrix/'aggregate.json').read_bytes()).hexdigest()};a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
