#!/usr/bin/env python3
"""Independent raw-only threshold replay audit; imports no candidate code."""
import hashlib,json,os
from pathlib import Path

ROOT=Path(__file__).resolve().parent
INP=ROOT/'input/a04'; FREEZE=json.loads((ROOT/'FREEZE.json').read_text())

def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while True:
   x=f.read(262144)
   if not x: break
   h.update(x)
 return h.hexdigest()

def sums(p):
 out={}
 for row in p.read_text().replace('\\n','\n').splitlines():
  h,name=row.split('  ',1);out[name]=h
 return out

def main():
 pm=sums(INP/'PACKAGE_SHA256SUMS.txt'); rm=sums(INP/'RAW_SHA256SUMS.txt')
 assert pm['results/RAW_SHA256SUMS.txt']==digest(INP/'RAW_SHA256SUMS.txt')
 assert pm['results/raw-a04.zip']==FREEZE['source_raw_archive_sha256']
 assert pm['SOURCE_MANIFEST.json']==digest(INP/'SOURCE_MANIFEST.json')
 for name in ('FREEZE.json','RESULT.json','AUDIT.json'):
  assert pm[name]==digest(INP/name)
 assert rm['runtime/events.jsonl']==digest(INP/'runtime/events.jsonl')==FREEZE['source_event_sha256']
 assert rm['report.json']==digest(INP/'report.json')==FREEZE['source_report_sha256']
 stream=[json.loads(s) for s in (INP/'runtime/events.jsonl').read_text().splitlines()]
 report=json.loads((INP/'report.json').read_text()); d=report['decisions'][5]
 c=d['final_action_admission']['action_validity']['contract']
 source=c['source']['signals']['health']['value']; start=d['controller_model_started_ns']; end=d['final_action_admission']['planner_terminal']['terminal_observed_ns']
 obs=[]
 for e in stream:
  if e.get('event')!='typed_observation': continue
  h=e.get('signals',{}).get('health',{}).get('value'); t=e.get('capture_ns')
  if type(h) is int and type(t) is int and start<t<=end: obs.append((t,e['sequence'],h))
 assert obs and all(obs[i][0]<obs[i+1][0] and obs[i][1]<obs[i+1][1] for i in range(len(obs)-1))
 bythreshold=[]
 for threshold in FREEZE['thresholds_health_loss_points']:
  cross=next((x for x in obs if source-x[2]>=threshold),None)
  bythreshold.append({'threshold_loss_points':threshold,'first_cross':None if cross is None else {
   'sequence':cross[1],'capture_ns':cross[0],'health':cross[2],'loss_points':source-cross[2],
   'elapsed_from_model_start_ms':round((cross[0]-start)/1000000,6),
   'remaining_to_planner_terminal_ms':round((end-cross[0])/1000000,6)}})
 outdir=Path(os.environ.get('RESULT_DIR',str(ROOT/'results/a01')))
 candidate_path=outdir/'candidate.json'
 result=json.loads(candidate_path.read_text())
 assert result['sweep']==bythreshold
 assert result['observations_during_pending_interval']==len(obs)
 assert result['existing_final_action_rule']['max_allowed_loss_points']==20
 assert result['existing_final_action_rule']['observed_final_health']==4
 assert result['existing_final_action_rule']['final_action_rejection_reason']=='health_max_decrease_from_source_failed'
 d4=report['decisions'][4]
 source=d4['cover_validity_admission']['source_signal']
 monitor=d4['policy_invalidation']['signals']['health']
 typed_by_seq={}
 for e in stream:
  if e.get('event')=='typed_observation':
   assert e['sequence'] not in typed_by_seq
   typed_by_seq[e['sequence']]=e
 source_event=typed_by_seq[source['sequence']]
 monitor_event=typed_by_seq[monitor['sequence']]
 source_raw=source_event['signals']['health']; monitor_raw=monitor_event['signals']['health']
 assert source_raw['signal_id']==monitor_raw['signal_id']=='health'
 assert source_raw['status']==monitor_raw['status']=='observed'
 assert source_raw['value']==source['value']==30
 assert monitor_raw['value']==monitor['value']==30
 assert source_event['capture_ns']==source['capture_ns']==source_raw['capture_ns']
 assert monitor_event['capture_ns']==monitor['capture_ns']==monitor_raw['capture_ns']
 assert source_event['sequence']==source['sequence'] and monitor_event['sequence']==monitor['sequence']
 reason=d4['policy_invalidation']['reason']
 assert reason=='health:source_expired'
 assert result['negative_control_decision4']['source_health']==source_raw['value']
 assert result['negative_control_decision4']['monitor_health']==monitor_raw['value']
 assert result['negative_control_decision4']['reason']==reason
 negative_control={'source_sequence':source['sequence'],'source_health':source_raw['value'],
  'source_capture_ns':source_raw['capture_ns'],'monitor_sequence':monitor['sequence'],
  'monitor_health':monitor_raw['value'],'monitor_capture_ns':monitor_raw['capture_ns'],
  'invalidation_reason':reason}
 out={'status':'PASS_A04_TRACE_REPLAY_AUDIT','checks':25,'observations':len(obs),
  'thresholds':len(bythreshold),'archive_sha256':FREEZE['source_raw_archive_sha256'],
  'candidate_sha256':digest(candidate_path),'negative_control_raw_join':negative_control}
 target=outdir/'audit.json'
 with target.open('x') as f: json.dump(out,f,indent=2);f.write('\n')
 print(json.dumps(out))
if __name__=='__main__': main()
