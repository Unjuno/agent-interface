#!/usr/bin/env python3
"""Independent first-outcome audit: no import from the experiment controller."""
import argparse, copy, hashlib, json
from collections import defaultdict
from pathlib import Path

def canonical(v): return json.dumps(v, sort_keys=True, separators=(',', ':'), allow_nan=False)
def sha(v): return hashlib.sha256(canonical(v).encode()).hexdigest()

def oracle(case):
    s, c = case['source'], case['current']
    action = 'act_A' if case['kind'] == 'overlap' or s['x'] < 0 else 'act_B'
    if case['kind'] == 'cert':
        control = c['x'] is not None and c['x'] != 0 and ((c['x'] < 0) == (s['x'] < 0))
    else: control = c['a'] == 0 and not (c['b'] == 1 and c['c'] == 1)
    ok = c['present'] is True and c['binding'] == s['binding'] and control and c['gA' if action=='act_A' else 'gB'] is True
    return bool(ok), action

def audit_row(r):
    expected, action = oracle(r['case'])
    receipt, adm = r['receipt'], r['admission']
    effects = r['effects']; executed = bool(effects)
    assert len(effects) <= 1 and r['execute_calls'] == len(effects)
    assert adm['eligible'] == executed
    assert not r['transaction_left_open']
    assert receipt['completed_transitions'] == len(effects)
    assert receipt['frontier_model_resumptions'] == 0
    assert receipt['input_authority'] == 'admission_per_action_only'
    assert receipt['elapsed_ns'] == receipt['ended_ns'] - receipt['started_ns'] >= 0
    observations = r['observations']
    assert [o['normalized']['sequence'] for o in observations] == list(range(1,len(observations)+1))
    assert receipt['observations'] == [{k:o['normalized'][k] for k in
        ('sequence','captured_ns','evidence_ref','evidence_digest','predicates')} for o in observations]
    for o in observations: assert o['normalized']['evidence_digest'] == sha(o['raw_world'])
    assert observations[0]['raw_world'] == r['case']['source']
    assert adm['final_world'] == r['case']['current'] and adm['transaction_open']
    if executed:
        assert effects[0]['action'] == action and effects[0]['pre_world'] == r['case']['current']
        assert receipt['outcome'] == 'TASK_SUCCEEDED' and receipt['reason']=='method_complete'
        auth = r['authority']; assert auth['used'] and auth['action'] == action
        token_data = {k:v for k,v in auth.items() if k!='token'}; token_data['used'] = False
        assert sha(token_data) == auth['token'] == adm['token']
        assert auth['source_sequence'] == 1 and auth['source_digest'] == observations[0]['normalized']['evidence_digest']
        assert auth['final_digest'] == sha(effects[0]['pre_world'])
        assert all(t['release_verified'] for t in receipt['transitions'])
        assert receipt['pending_effect'] is None
    else:
        assert receipt['outcome'] == 'SAFE_YIELD'
        assert r['authority'] is None and not receipt['transitions']
    if r['mode'] in ('unique','certified'): assert executed == expected
    if r['mode']=='certified':
        assert adm['strategy'] == ('selected_when' if r['certificate']['exclusive'] else 'full_unique')
    return expected, executed

def main():
    p=argparse.ArgumentParser();p.add_argument('directory',type=Path);a=p.parse_args()
    rows=[json.loads(line) for line in (a.directory/'raw.jsonl').read_text().splitlines()]
    assert len(rows)==736 and len({r['id'] for r in rows})==736
    summaries=defaultdict(lambda:dict(rows=0,allowed=0,executed=0,stale=0,false_stop=0))
    compare=defaultdict(dict)
    for r in rows:
        expected,actual=audit_row(r)
        s=summaries[r['case']['suite']+'/'+r['mode']]
        s['rows']+=1;s['allowed']+=expected;s['executed']+=actual
        s['stale']+=int(actual and not expected);s['false_stop']+=int(expected and not actual)
        if r['mode'] in ('unique','certified'):
            compare[r['id'].split('-')[0]][r['mode']] = (r['receipt']['outcome'],r['receipt']['reason'],r['effects'])
    assert len(compare)==168
    assert all(v['unique']==v['certified'] for v in compare.values())
    assert summaries['cert_grid/union']['false_stop']>0 and summaries['cert_grid/naive']['stale']>0
    assert summaries['overlap/unchecked_selected']['stale']>0
    good=next(r for r in rows if r['mode']=='certified' and r['effects'])
    rejected=[]
    for label in ('digest','effect_action','receipt_count','authority_sequence'):
        bad=copy.deepcopy(good)
        if label=='digest':bad['observations'][0]['normalized']['evidence_digest']='0'*64
        elif label=='effect_action':bad['effects'][0]['action']='act_B' if bad['effects'][0]['action']=='act_A' else 'act_A'
        elif label=='receipt_count':bad['receipt']['completed_transitions']=7
        else:bad['authority']['source_sequence']=2
        try:audit_row(bad)
        except AssertionError:rejected.append(label)
    assert len(rejected)==4
    result=dict(status='PASS_FINITE_EXACT_RUNTIME_GATE',rows=len(rows),
        unique_vs_certified_pairs=len(compare),mutation_audit_rejected=rejected,groups=dict(sorted(summaries.items())),
        raw_sha256=hashlib.sha256((a.directory/'raw.jsonl').read_bytes()).hexdigest(),
        limitations=['finite cooperative SQLite adapter','no model/GUI or physical input','virtual clock, no speed result'])
    (a.directory/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
