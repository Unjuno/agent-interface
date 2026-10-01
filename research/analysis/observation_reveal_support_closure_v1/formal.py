from __future__ import annotations
from itertools import product
import argparse,hashlib,json
from pathlib import Path
from candidate import (
    UNCHANGED,IRRELEVANT_CHANGE,DUPLICATE_TARGET,
    VALID_CROP,TARGET_REMOVED,TARGET_CHANGED,
    required_reuse,crop_only,support_closure,
)

TASK='OBSERVATION-GATING-O3-REVEAL-SUPPORT-CLOSURE-20260919-001'
STATES=(UNCHANGED,IRRELEVANT_CHANGE,DUPLICATE_TARGET)


def analytic_witness():
    crop=('target-signature','context')
    return {
      'crop_visible_evidence_identical':True,
      'w0_crop':crop,'w1_crop':crop,
      'w0_outside':'IRRELEVANT_CHANGE',
      'w1_outside':'DUPLICATE_TARGET',
      'w0_required':'REUSE_CONTEXT',
      'w1_required':'RAW_FALLBACK',
      'required_decisions_differ':True,
    }


def construction():
    base=(UNCHANGED,)*10
    deco=(IRRELEVANT_CHANGE,)+base[1:]
    dupe=(DUPLICATE_TARGET,)+base[1:]
    rows=[]
    cases=[
      ('irrelevant_outside',dict(source_current=True,critical_event=False,outside_states=deco,crop_state=VALID_CROP,uniqueness_bound=True)),
      ('duplicate_outside',dict(source_current=True,critical_event=False,outside_states=dupe,crop_state=VALID_CROP,uniqueness_bound=True)),
      ('critical',dict(source_current=True,critical_event=True,outside_states=base,crop_state=VALID_CROP,uniqueness_bound=True)),
      ('stale_source',dict(source_current=False,critical_event=False,outside_states=base,crop_state=VALID_CROP,uniqueness_bound=True)),
      ('target_removed',dict(source_current=True,critical_event=False,outside_states=base,crop_state=TARGET_REMOVED,uniqueness_bound=True)),
      ('target_changed',dict(source_current=True,critical_event=False,outside_states=base,crop_state=TARGET_CHANGED,uniqueness_bound=True)),
      ('forged_uniqueness',dict(source_current=True,critical_event=False,outside_states=base,crop_state=VALID_CROP,uniqueness_bound=False)),
    ]
    for name,kw in cases:
        b=crop_only(**{k:v for k,v in kw.items() if k!='uniqueness_bound'})
        c=support_closure(**kw)
        truth=required_reuse(**{k:v for k,v in kw.items() if k!='uniqueness_bound'})
        rows.append({'name':name,'required_reuse':truth,'baseline':b,'candidate':c})
    ok=(
      rows[0]['candidate']['action']=='REUSE_CONTEXT' and
      rows[1]['baseline']['action']=='REUSE_CONTEXT' and rows[1]['candidate']['action']=='RAW_FALLBACK' and
      rows[2]['candidate']['action']=='FORWARD_CRITICAL' and
      rows[3]['candidate']['action']=='STALE_SOURCE_REJECTED' and
      rows[4]['candidate']['action']=='RAW_FALLBACK' and rows[5]['candidate']['action']=='RAW_FALLBACK' and
      rows[6]['candidate']['action']=='UNIQUENESS_RECEIPT_REJECTED'
    )
    malformed=[]
    for name,fn in [
      ('bad_count',lambda:support_closure(source_current=True,critical_event=False,outside_states=(UNCHANGED,),uniqueness_bound=True)),
      ('bad_state',lambda:support_closure(source_current=True,critical_event=False,outside_states=('BAD',)*10,uniqueness_bound=True)),
      ('bad_binding',lambda:support_closure(source_current=True,critical_event=False,outside_states=base,uniqueness_bound='yes')),
    ]:
        try: fn(); malformed.append({'name':name,'rejected':False})
        except ValueError: malformed.append({'name':name,'rejected':True})
    return {'task':TASK,'phase':'construction','formal_invocations':0,'rows':rows,'malformed':malformed,'pass':ok and all(x['rejected'] for x in malformed),'analytic':analytic_witness()}


def formal(source_sha256:dict):
    m={
      'rows':0,'baseline_false_suppressions':0,'baseline_safe_reuses':0,
      'candidate_false_suppressions':0,'candidate_safe_reuses':0,
      'candidate_ambiguity_raw_fallbacks':0,'candidate_critical_forwards_current':0,
      'candidate_stale_source_fallbacks':0,
    }
    digest=hashlib.sha256(); examples=[]
    for outside in product(STATES, repeat=10):
      has_dupe=DUPLICATE_TARGET in outside
      for critical in (False,True):
        for current in (False,True):
          truth=required_reuse(source_current=current,critical_event=critical,outside_states=outside)
          b=crop_only(source_current=current,critical_event=critical,outside_states=outside)
          c=support_closure(source_current=current,critical_event=critical,outside_states=outside,uniqueness_bound=True)
          breuse=b['action']=='REUSE_CONTEXT'; creuse=c['action']=='REUSE_CONTEXT'
          m['rows']+=1
          m['baseline_false_suppressions']+=int(breuse and not truth)
          m['baseline_safe_reuses']+=int(breuse and truth)
          m['candidate_false_suppressions']+=int(creuse and not truth)
          m['candidate_safe_reuses']+=int(creuse and truth)
          m['candidate_ambiguity_raw_fallbacks']+=int(current and not critical and has_dupe and c['action']=='RAW_FALLBACK' and c['reason']=='AMBIGUOUS_TARGET')
          m['candidate_critical_forwards_current']+=int(current and critical and c['action']=='FORWARD_CRITICAL')
          m['candidate_stale_source_fallbacks']+=int((not current) and c['action']=='STALE_SOURCE_REJECTED')
          row=(outside,critical,current,truth,b['action'],c['action'],c['reason'])
          digest.update(json.dumps(row,separators=(',',':')).encode())
          if breuse and not truth and len(examples)<8:
            examples.append({'outside':outside,'critical':critical,'current':current})
    return {
      'task':TASK,'phase':'formal','formal_invocations':1,'reruns':0,'replacements':0,'tuning':0,
      'source_sha256':source_sha256,'analytic':analytic_witness(),'metrics':m,
      'ledger_sha256':digest.hexdigest(),'examples':examples,
    }


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=['construction','formal'],required=True);ap.add_argument('--source-manifest');ap.add_argument('--out',required=True);a=ap.parse_args()
    if a.phase=='construction': r=construction()
    else:
      if not a.source_manifest: raise SystemExit('--source-manifest required')
      r=formal(json.loads(Path(a.source_manifest).read_text())['sha256'])
    Path(a.out).write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'phase':r['phase'],'pass':r.get('pass'),'metrics':r.get('metrics')},sort_keys=True))
if __name__=='__main__':main()
