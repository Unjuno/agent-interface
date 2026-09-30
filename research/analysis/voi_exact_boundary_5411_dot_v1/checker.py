"""Read-only retained-result arithmetic check; never imports predecessor code."""
import argparse
import base64
import gzip
import hashlib
import itertools
import json
import os
from pathlib import Path
import resource
import signal
import sys
import time
from fractions import Fraction as Q

EPS=Q(1,10**12)
EXPECTED_RAW='fa237492dd6657da2b98a3b48bc994851e057a70df1c252fbe974a2a5ea22f3a'
GRID=(('0.2','0.4','0.6','0.8','0.95'),('1','4','16'),('0.6','0.8','1'),('0','0.1','0.3'),('0','0.05','0.2'))
INPUT_KEYS=('p_safe','loss','sensitivity','false_pass','delay_cost')
NUMERIC_KEYS=('action_value','stop_value','pass_value','fail_value','test_value','continue_value','net_voi','option_premium','premium_continue_value')

def exact_values(p,loss,sensitivity,false_pass,delay,eps=EPS):
    # Joint safe/unsafe mass for each observation; optimize admit/yield per branch.
    action=p-loss*(1-p)
    branches=((p*sensitivity,(1-p)*false_pass),
              (p*(1-sensitivity),(1-p)*(1-false_pass)))
    utilities=[max(Q(0),safe-loss*unsafe) for safe,unsafe in branches]
    stop=max(Q(0),action); test=sum(utilities,Q(0)); wait=test-delay
    premium=(1-p)*loss if action>eps else Q(0)
    return dict(action_value=action,stop_value=stop,pass_value=utilities[0],fail_value=utilities[1],
                test_value=test,continue_value=wait,net_voi=wait-stop,option_premium=premium,
                premium_continue_value=wait+premium)

def decisions(v,eps):
    cont=v['continue_value']-v['stop_value']>eps
    premium=v['premium_continue_value']-v['stop_value']>eps
    return dict(immediate_action='ADMIT' if v['action_value']>eps else 'YIELD',
                voi_decision='CONTINUE' if cont else 'STOP',bellman_decision='CONTINUE' if cont else 'STOP',
                premium_decision='CONTINUE' if premium else 'STOP',
                premium_dominated_wait=premium and v['continue_value']-v['stop_value'] < -eps)

def predicate_types_valid(value):
    return all(type(value[k]) is str for k in ('immediate_action','voi_decision','bellman_decision','premium_decision')) and type(value['premium_dominated_wait']) is bool

def text_q(q):return str(q.numerator)+'/'+str(q.denominator)
def digest(b):return hashlib.sha256(b).hexdigest()
def write_json(path,value):path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')

def inspect(raw):
    assert raw['schema']=='voi_option_5306_t1_raw_v1','raw_schema'
    assert raw['base_main_sha']=='6b1ad36c0628098c2d1c28b0a1b371db099aecce','raw_base'
    expected=list(itertools.product(*GRID)); rows=raw['rows'];assert len(rows)==len(expected)==405,'row_count'
    expected_grid={k:[Q(s) for s in choices] for k,choices in zip(INPUT_KEYS,GRID)}
    assert {k:[Q(str(x)) for x in raw['grid'][k]] for k in INPUT_KEYS}==expected_grid,'declared_grid'
    assert raw['grid_sha256']==digest(json.dumps(raw['grid'],sort_keys=True,separators=(',',':')).encode()),'grid_digest'
    output=[]; mismatches=[]; rounding=[]; semantic=[]; numeric_failures=[]; source_predicate_mismatch=[]; type_mismatches=[]
    ties={k:[] for k in ('immediate','voi','premium')}; positives=[]; seen=set(); maximum=Q(0)
    exact_changes=exact_dominated=0; exact_premium_ties=[]
    for index,(row,values) in enumerate(zip(rows,expected)):
        cid='voi-option-'+str(index).zfill(3);assert row['case_id']==cid and cid not in seen,'ordered_unique_ids';seen.add(cid)
        inp=tuple(Q(s) for s in values)
        assert tuple(Q(str(row['inputs'][k])) for k in INPUT_KEYS)==inp,'exact_input_coverage'
        v=exact_values(*inp); strict_v=exact_values(*inp,eps=Q(0))
        declared=decisions(v,EPS);strict=decisions(strict_v,Q(0))
        observed={k:row[k] for k in declared}
        if not predicate_types_valid(observed):type_mismatches.append(cid)
        for k in declared:
            if observed[k]!=declared[k]:mismatches.append({'case_id':cid,'field':k,'observed':observed[k],'exact_declared':declared[k]})
            if declared[k]!=strict[k]:semantic.append({'case_id':cid,'field':k,'declared':declared[k],'strict':strict[k]})
        # Reconstruct the source's actual threshold-expression spelling on retained doubles.
        actual=dict(immediate_action='ADMIT' if row['action_value']>1e-12 else 'YIELD',
                    voi_decision='CONTINUE' if row['continue_value']>row['stop_value']+1e-12 else 'STOP',
                    bellman_decision='CONTINUE' if row['continue_value']>row['stop_value']+1e-12 else 'STOP',
                    premium_decision='CONTINUE' if row['premium_continue_value']>row['stop_value']+1e-12 else 'STOP',
                    premium_dominated_wait=row['premium_continue_value']>row['stop_value']+1e-12 and row['continue_value']<row['stop_value']-1e-12)
        for k in actual:
            if actual[k]!=observed[k]:source_predicate_mismatch.append({'case_id':cid,'field':k})
        errors={k:Q.from_float(float(row[k]))-v[k] for k in NUMERIC_KEYS}
        for k,e in errors.items():
            maximum=max(maximum,abs(e))
            if e:rounding.append({'case_id':cid,'field':k,'signed_binary_error':text_q(e)})
            if abs(Q(str(row[k]))-v[k])>Q(1,10**10):numeric_failures.append({'case_id':cid,'field':k})
        margins={'immediate':v['action_value'],'voi':v['net_voi'],'premium':v['premium_continue_value']-v['stop_value']}
        for k,m in margins.items():
            if m==0:ties[k].append(cid)
            else:positives.append(abs(m))
        exact_changes+=declared['premium_decision']!=declared['voi_decision']
        exact_dominated+=declared['premium_dominated_wait']
        if declared['premium_decision']!=declared['voi_decision'] and v['net_voi']==0:exact_premium_ties.append(cid)
        output.append({'case_id':cid,'inputs':dict(zip(INPUT_KEYS,values)),
            'exact_values':{k:text_q(x) for k,x in v.items()},'exact_margins':{k:text_q(x) for k,x in margins.items()},
            'exact_declared_decisions':declared,'exact_strict_decisions':strict,'retained_decisions':observed,
            'signed_binary_errors':{k:text_q(x) for k,x in errors.items()}})
    expected_summary={'case_count':405,'voi_bellman_mismatches':0,'premium_decision_changes':exact_changes,'premium_dominated_waits':exact_dominated}
    retained_identity_error=max(abs(r['net_voi']-(r['continue_value']-r['stop_value'])) for r in rows)
    expected_summary['max_voi_value_identity_error']=retained_identity_error
    summary_mismatch={k:{'recorded':raw['summary'].get(k),'exact':v} for k,v in expected_summary.items() if raw['summary'].get(k)!=v}
    result={'disposition':'PASS_NO_DECLARED_DECISION_DISCREPANCY' if not (mismatches or numeric_failures or source_predicate_mismatch or summary_mismatch or type_mismatches) else 'FAIL_RETAINED_EXACT_COMPARISON',
        'rows':405,'numeric_values_compared':405*len(NUMERIC_KEYS),'discrepancies':mismatches,
        'source_predicate_mismatches':source_predicate_mismatch,'declared_vs_strict_differences':semantic,
        'predicate_type_mismatches':type_mismatches,'retained_max_voi_identity_error':retained_identity_error,
        'numeric_tolerance_failures':numeric_failures,'aggregate_mismatches':summary_mismatch,
        'exact_summary':expected_summary,'exact_zero_ties':ties,'premium_changed_exact_ties':exact_premium_ties,
        'minimum_nonzero_absolute_decision_margin':text_q(min(positives)),
        'all_margins_on_1_over_200_lattice':all((x*200).denominator==1 for x in positives),
        'maximum_absolute_binary_value_error':text_q(maximum),'nonzero_binary_rounding_entries':len(rounding),
        'all_nonzero_rounding_entries':rounding,'declared_epsilon':text_q(EPS),'strict_epsilon':'0/1',
        'scope':'retained_finite_grid_arithmetic_only; no predecessor rerun or live system claim'}
    return result,output

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);args=ap.parse_args()
    resource.setrlimit(resource.RLIMIT_AS,(128*1024*1024,128*1024*1024))
    resource.setrlimit(resource.RLIMIT_CPU,(9,10))
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('10_second_wall_bound')))
    signal.setitimer(signal.ITIMER_REAL,10)
    if hasattr(os,'sched_setaffinity'):os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
    root=Path(__file__).resolve().parent;out=Path(args.out);out.mkdir(exist_ok=False)
    start=time.monotonic_ns();write_json(out/'STARTED.json',{'allocation':'dot-5411-exact-raw-20260930-01','pid':os.getpid(),'started_wall_ns':time.time_ns()})
    try:
        freeze=json.loads((root/'FREEZE.json').read_text())
        for name,want in freeze['files'].items():assert digest((root/name).read_bytes())==want,'source_hash:'+name
        encoded=(root/'inputs/results__formal-01__raw.json.gz.b64').read_bytes()
        data=gzip.decompress(base64.b64decode(b''.join(encoded.split()),validate=True))
        assert len(data)==198339 and digest(data)==EXPECTED_RAW,'retained_raw_integrity'
        result,rows=inspect(json.loads(data))
        with (out/'EXACT_ROWS.jsonl').open('x') as f:
            for row in rows:f.write(json.dumps(row,sort_keys=True,separators=(',',':'))+'\n')
        result.update(raw_sha256=digest(data),source_freeze_sha256=digest((root/'FREEZE.json').read_bytes()),
                      elapsed_ns=time.monotonic_ns()-start,max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                      process_cpu_seconds=time.process_time(),python=sys.version,uname=list(os.uname()),
                      affinity=sorted(os.sched_getaffinity(0)),address_space_limit=resource.getrlimit(resource.RLIMIT_AS),
                      wall_limit_seconds=10,experimental_invocations=1,predecessor_invocations=0)
        write_json(out/'RESULT.json',result)
        write_json(out/'SHA256.json',{p.name:digest(p.read_bytes()) for p in out.iterdir() if p.is_file()})
        print(json.dumps({k:v for k,v in result.items() if k not in ('all_nonzero_rounding_entries','exact_zero_ties','premium_changed_exact_ties')},sort_keys=True))
        return int(result['disposition'].startswith('FAIL'))
    except Exception as e:
        write_json(out/'STOP.json',{'disposition':'STOP_FIRST_OUTCOME','error_type':type(e).__name__,'error':str(e),'elapsed_ns':time.monotonic_ns()-start})
        raise
    finally:signal.setitimer(signal.ITIMER_REAL,0)

if __name__=='__main__':raise SystemExit(main())
