import argparse,hashlib,json
from pathlib import Path
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--aggregate',required=True);ap.add_argument('--freeze',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();r=json.loads(Path(a.aggregate).read_text());f=json.loads(Path(a.freeze).read_text())
 checks={'decision':r['decision']=='PASS_MATCHED_SOURCE_TEMPORAL_QUERY_BATCHED_SCOPED','n':r['histories']==220000,'batches':r['formal_batches']==20 and r['batch_size']==11000,'formal':r['formal_invocations']==1 and r['reruns']==0,'oracle':r['candidate_oracle_mismatches']==0,'leaks':not any(r['leaks'].values()),'noninferiority':not r['query_worse_classes'],'advantage':r['overall_advantage_pp']>=15,'authority':r['grants_input_authority'] is False,'source_batch':h('batch_experiment.py')==f['sha256']['batch_experiment.py'],'source_aggregate':h('aggregate.py')==f['sha256']['aggregate.py'],'source_audit':h('audit.py')==f['sha256']['audit.py'],'source_plan':h('PLAN.md')==f['sha256']['PLAN.md']}
 out={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'aggregate_sha256':h(a.aggregate),'freeze_sha256':h(a.freeze)};Path(a.output).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True));raise SystemExit(0 if out['status']=='PASS' else 1)
if __name__=='__main__':main()
