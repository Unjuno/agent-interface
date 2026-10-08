#!/usr/bin/env python3
"""Posthoc first-cross timing sweep over the retained V39 A04 health trace."""
import hashlib,json,os
from pathlib import Path

HERE=Path(__file__).resolve().parent
INPUT=HERE/'input/a04'
FREEZE=json.loads((HERE/'FREEZE.json').read_text())

def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(1<<20),b''): h.update(block)
 return h.hexdigest()

def checksum_map(path):
 result={}
 for line in path.read_text().replace('\\n','\n').splitlines():
  digest,rel=line.split('  ',1);result[rel]=digest
 return result

def read_inputs():
 raw_sums=INPUT/'RAW_SHA256SUMS.txt'; package_sums=INPUT/'PACKAGE_SHA256SUMS.txt'
 rs=checksum_map(raw_sums); ps=checksum_map(package_sums)
 assert ps['results/RAW_SHA256SUMS.txt']==sha(raw_sums)
 assert ps['results/raw-a04.zip']==FREEZE['source_raw_archive_sha256']
 events=INPUT/'runtime/events.jsonl'; report=INPUT/'report.json'
 assert rs['runtime/events.jsonl']==sha(events)==FREEZE['source_event_sha256']
 assert rs['report.json']==sha(report)==FREEZE['source_report_sha256']
 rows=[json.loads(line) for line in events.read_text().splitlines()]
 doc=json.loads(report.read_text())
 return rows,doc

def first_cross(rows, source_health, threshold, start_ns, terminal_ns):
 for event in rows:
  if event.get('event')!='typed_observation': continue
  capture=event.get('capture_ns'); health=event.get('signals',{}).get('health',{}).get('value')
  if type(capture) is not int or type(health) is not int: continue
  if not start_ns < capture <= terminal_ns: continue
  if source_health-health >= threshold:
   return {'sequence':event['sequence'],'capture_ns':capture,'health':health,
           'loss_points':source_health-health,'elapsed_from_model_start_ms':round((capture-start_ns)/1e6,6),
           'remaining_to_planner_terminal_ms':round((terminal_ns-capture)/1e6,6)}
 return None

def main():
 rows,report=read_inputs(); decision=report['decisions'][FREEZE['decision_index']]
 contract=decision['final_action_admission']['action_validity']['contract']
 source=contract['source']['signals']['health']['value']; start=FREEZE['model_pending_interval_ns']['start']
 terminal=FREEZE['model_pending_interval_ns']['planner_terminal_observed']
 points=[]
 for threshold in FREEZE['thresholds_health_loss_points']:
  points.append({'threshold_loss_points':threshold,'first_cross':first_cross(rows,source,threshold,start,terminal)})
 result={'schema':'map01-v39-unauthored-coast-health-threshold-replay-result-v1',
  'status':'PASS_A04_TRACE_REPLAY','source_health':source,'source_sequence':contract['source']['sequence'],
  'model_start_ns':start,'planner_terminal_observed_ns':terminal,
  'observations_during_pending_interval':sum(1 for r in rows if r.get('event')=='typed_observation' and start<r.get('capture_ns',0)<=terminal),
  'sweep':points,
  'existing_final_action_rule':{'operator':'max_decrease_from_source > max_allowed causes rejection',
    'max_allowed_loss_points':next(p['value'] for p in contract['predicates'] if p.get('operator')=='max_decrease_from_source'),
    'observed_final_health':decision['final_action_admission']['action_validity']['snapshot']['signals']['health']['value'],
    'final_action_rejection_reason':decision['final_action_admission']['action_validity']['reason']},
  'negative_control_decision4':{'source_sequence':report['decisions'][4]['cover_validity_admission']['source_signal']['sequence'],
    'source_health':report['decisions'][4]['cover_validity_admission']['source_signal']['value'],
    'monitor_health':report['decisions'][4]['policy_invalidation']['signals']['health']['value'],
    'reason':report['decisions'][4]['policy_invalidation']['reason'],
    'interpretation':'no health-loss threshold would fire at its recorded cancellation observation'},
  'scope':'one posthoc trace; no interruption was enacted; timing only'}
 out=Path(os.environ.get('RESULT_DIR',str(HERE/'results/a01')));out.mkdir(parents=True,exist_ok=True)
 target=out/'candidate.json'
 with target.open('x') as f: json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps({'status':result['status'],'sweep':points,'output':str(target)}))
if __name__=='__main__': main()
