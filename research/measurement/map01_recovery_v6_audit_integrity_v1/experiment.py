from __future__ import annotations
import argparse,ast,hashlib,json,os,shutil,subprocess,sys,tempfile
from pathlib import Path
from binding_guard import binding_failures

TASK='MAP01-RECOVERY-V6-AUDIT-INTEGRITY-20260918-001'
ALLOCATION='map01-recovery-cover-mechanism-live-v6-01'
PHASE='immediately_after_delay_before_fallback_cleanup'
EXPECTED_GIT_BLOBS={
 'audit_map01_recovery_cover_mechanism_v4.py':'c193b8e985b5e047d4a28f8f04b2ccaf60daac12',
 'audit_map01_recovery_cover_mechanism_v6.py':'e3c34caad26a5a7e17d2464c945b74f747b75d4b',
}

def git_blob_sha(path:Path)->str:
    b=path.read_bytes();return hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()

def sha256(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()
def writej(path:Path,v)->None:path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def writejl(path:Path,rows)->None:path.parent.mkdir(parents=True,exist_ok=True);path.write_text(''.join(json.dumps(x,sort_keys=True)+'\n' for x in rows),encoding='utf-8')

def tree_digest(root:Path,exclude_names=frozenset({'summary.json','formal-audit.json'}))->str:
    h=hashlib.sha256()
    for p in sorted(x for x in root.rglob('*') if x.is_file() and x.name not in exclude_names):
        rel=p.relative_to(root).as_posix().encode();b=p.read_bytes();h.update(len(rel).to_bytes(4,'big'));h.update(rel);h.update(len(b).to_bytes(8,'big'));h.update(b)
    return h.hexdigest()

def static_check(source_dir:Path)->dict:
    p=source_dir/'audit_map01_recovery_cover_mechanism_v4.py';text=p.read_text(encoding='utf-8');ast.parse(text)
    return {
      'pair_coast_read':'pair.get("coast_no_retained_input_upper_ns")' in text,
      'pair_recovery_read':'pair.get("recovery_no_retained_input_upper_ns")' in text,
      'arm_bounds_read':'bounds = arm_summary.get("input_bounds") or {}' in text,
      'arm_no_input_numeric_read':'bounds.get("no_retained_input_upper_bound_ns")' in text,
    }

def build_case(root:Path,summary_recovery_ns:int=570_000_000)->None:
    root.mkdir(parents=True,exist_ok=False)
    writej(root/'construction.json',{'allocation_id':ALLOCATION,'model_calls':0,'planner_wait_ms':600})
    pairs=[]
    for i in (1,2,3):
        coast=600_000_000; recovery=570_000_000
        pairs.append({'pair_index':i,'failures':[],'coast_no_retained_input_upper_ns':coast,'recovery_no_retained_input_upper_ns':summary_recovery_ns,'recovery_positive_event_count':0,'recovery_negative_event_count':0})
        for arm,no_input,admissions in (('coast_control',coast,0),('bounded_recovery',recovery,1)):
            ar=root/f'pair-{i:02d}'/arm;rt=ar/'runtime'
            writejl(rt/'events.jsonl',[]);writejl(rt/'delivered.jsonl',[])
            writej(rt/'scorer-summary.json',{'scheduler':{'missed_sample_periods':0}})
            writej(ar/'terminal-score-audit.json',{'pass':True})
            writej(ar/'arm-summary.json',{
              'terminal_release_verified':True,
              'planner_window':{'duration_ns':600_000_000,'end_boundary_phase':PHASE},
              'input_bounds':{'valid':True,'admission_count':admissions,'measurement_class':'SYNTHETIC_VALID','no_retained_input_upper_bound_ns':no_input}
            })
    writej(root/'summary.json',{'pairs':pairs})

def run_retained_audit(source_dir:Path,case_root:Path)->tuple[int,dict]:
    out=case_root/'formal-audit.json';env=os.environ.copy();env['PYTHONPATH']=str(source_dir)
    cp=subprocess.run([sys.executable,str(source_dir/'audit_map01_recovery_cover_mechanism_v6.py'),str(case_root),'--out',str(out)],env=env,text=True,capture_output=True)
    if not out.exists(): raise RuntimeError(f'audit produced no output rc={cp.returncode} stderr={cp.stderr}')
    return cp.returncode,json.loads(out.read_text(encoding='utf-8'))

def main(source_dir:Path,out_path:Path)->dict:
    source_dir=source_dir.resolve();ids={k:git_blob_sha(source_dir/k) for k in EXPECTED_GIT_BLOBS}
    if ids!=EXPECTED_GIT_BLOBS: raise RuntimeError(f'source identity mismatch: {ids}')
    static=static_check(source_dir)
    with tempfile.TemporaryDirectory() as td:
        td=Path(td);truth=td/'truth';build_case(truth,570_000_000)
        corrupt=td/'summary_corrupt';shutil.copytree(truth,corrupt);(corrupt/'formal-audit.json').unlink(missing_ok=True)
        s=json.loads((corrupt/'summary.json').read_text());
        for p in s['pairs']:p['recovery_no_retained_input_upper_ns']=480_000_000
        writej(corrupt/'summary.json',s)
        identical_non_summary=(tree_digest(truth)==tree_digest(corrupt))
        truth_guard=binding_failures(truth);corrupt_guard=binding_failures(corrupt)
        rc_t,a_t=run_retained_audit(source_dir,truth);rc_c,a_c=run_retained_audit(source_dir,corrupt)
        invalid=td/'invalid_arm';shutil.copytree(truth,invalid);(invalid/'formal-audit.json').unlink(missing_ok=True)
        p=invalid/'pair-01'/'bounded_recovery'/'arm-summary.json';v=json.loads(p.read_text());v['input_bounds']['valid']=False;writej(p,v)
        rc_i,a_i=run_retained_audit(source_dir,invalid)
        phase=td/'wrong_phase';shutil.copytree(truth,phase);(phase/'formal-audit.json').unlink(missing_ok=True)
        p=phase/'pair-01'/'coast_control'/'arm-summary.json';v=json.loads(p.read_text());v['planner_window']['end_boundary_phase']='after_cleanup';writej(p,v)
        rc_p,a_p=run_retained_audit(source_dir,phase)
        confirmed=(identical_non_summary and not truth_guard and bool(corrupt_guard) and rc_t==0 and rc_c==0 and a_t.get('valid_experiment') is True and a_c.get('valid_experiment') is True and a_t.get('decision')=='HOLD' and a_c.get('decision')=='PASS_MECHANISM_ONLY' and rc_i!=0 and a_i.get('decision')=='FAIL' and rc_p!=0 and a_p.get('decision')=='FAIL' and static['arm_no_input_numeric_read'] is False)
        result={
          'schema':'map01-recovery-v6-audit-integrity-result-v1','task':TASK,
          'source_git_blobs':ids,'static_source_check':static,
          'truth':{'summary_sha256':sha256(truth/'summary.json'),'non_summary_tree_sha256':tree_digest(truth),'guard_failures':truth_guard,'audit_rc':rc_t,'decision':a_t.get('decision'),'valid_experiment':a_t.get('valid_experiment'),'paired_median_reduction_fraction':a_t.get('paired_median_reduction_fraction'),'hard_failures':a_t.get('hard_failures')},
          'summary_only_corrupt':{'summary_sha256':sha256(corrupt/'summary.json'),'non_summary_tree_sha256':tree_digest(corrupt),'guard_failures':corrupt_guard,'audit_rc':rc_c,'decision':a_c.get('decision'),'valid_experiment':a_c.get('valid_experiment'),'paired_median_reduction_fraction':a_c.get('paired_median_reduction_fraction'),'hard_failures':a_c.get('hard_failures')},
          'controls':{'invalid_arm':{'audit_rc':rc_i,'decision':a_i.get('decision'),'valid_experiment':a_i.get('valid_experiment'),'hard_failures':a_i.get('hard_failures')},'wrong_phase':{'audit_rc':rc_p,'decision':a_p.get('decision'),'valid_experiment':a_p.get('valid_experiment'),'hard_failures':a_p.get('hard_failures')}},
          'identical_non_summary_tree':identical_non_summary,
          'decision':'CONFIRMED_V6_SUMMARY_ARM_BINDING_GAP' if confirmed else 'REFUTED_V6_SUMMARY_ARM_BINDING_GAP',
          'claim_scope':'retained-audit artifact integrity only; no live recovery efficacy/timing claim'
        }
    out_path.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8');print(json.dumps(result,indent=2,sort_keys=True));return result

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source-dir',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();main(a.source_dir,a.out)
