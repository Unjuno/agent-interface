#!/usr/bin/env python3
import copy, hashlib, json
from pathlib import Path
ROOT=Path('/mnt/data/libreoffice_conflict_c254')
SUMMARY=ROOT/'scored-pair-03'/'SUMMARY.json'
EXPECTED_RUNNER='b88c328f5567bc7f83e6fb014fe19c1644da798b62eb17f226c8314511ca2cb1'
EXPECTED_SCORER='cb22bd2ab6f55c5c99a9135417b511d683fc519b193c809dedefe6ed23e6cc7a'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def validate(d):
    errs=[]
    if d.get('allocation')!='c254-pair-03': errs.append('allocation')
    if d.get('order')!=['stable','inplace']: errs.append('order')
    rows={r['arm']:r for r in d.get('rows',[])}
    if set(rows)!={'stable','inplace'}: return errs+['arms']
    s=rows['stable']; r=rows['inplace']
    for x in (s,r):
        if x['precheck']['focus_id']!=x['calc_window_id']: errs.append(x['arm']+':focus')
        if not (x['precheck']['monotonic_ns'] < x['before_save']['monotonic_ns'] < x['after_ctrl_s']['monotonic_ns'] < x['after_optional_format_confirm']['monotonic_ns'] <= x['release']['monotonic_ns']): errs.append(x['arm']+':ordering')
        if x['after_ctrl_s']['modal_names'] != ['Confirm File Format']: errs.append(x['arm']+':format_modal')
        if x['format_confirm_enter_sent'] is not True: errs.append(x['arm']+':format_enter')
        if x['release']['verified'] is not True or x['release']['keys_down'] or x['release']['buttons_down']: errs.append(x['arm']+':release')
        if x['score']['sha256']!=x['after_optional_format_confirm']['file']['sha256']: errs.append(x['arm']+':score_hash')
    if s['classification']!='stable_saved' or s['after_optional_format_confirm']['modal_names']!=[]: errs.append('stable:class_or_modal')
    if s['score']['cells']!={'A1':'office','A2':'preview','A3':None,'B1':None}: errs.append('stable:cells')
    ai=r.get('after_external_inplace')
    if not ai: errs.append('inplace:no_mutation')
    else:
        if ai['file']['ino'] != r['precheck']['file']['ino'] or ai['pre_inode'] != r['precheck']['file']['ino']: errs.append('inplace:inode_changed')
        if ai['file']['sha256'] != r['replacement_source']['sha256']: errs.append('inplace:payload_hash')
        if not (r['precheck']['monotonic_ns'] < ai['monotonic_ns'] < r['before_save']['monotonic_ns']): errs.append('inplace:mutation_order')
        if r['before_save']['file']['sha256']!=ai['file']['sha256']: errs.append('inplace:pre_save_changed')
    if r['classification']!='inplace_external_preserved_with_prompt': errs.append('inplace:class')
    if r['after_optional_format_confirm']['modal_names']!=['Document Has Been Changed by Others']: errs.append('inplace:conflict_modal')
    if r['score']['cells']!={'A1':'external','A2':'replacement','A3':'external-marker','B1':'writer'}: errs.append('inplace:cells')
    if r['score']['sha256']!=r['after_external_inplace']['file']['sha256']: errs.append('inplace:not_preserved')
    return errs

d=json.loads(SUMMARY.read_text()); errors=[]
if sha(ROOT/'pair_runner_inplace.py')!=EXPECTED_RUNNER: errors.append('runner_hash')
if sha(ROOT/'score_any.py')!=EXPECTED_SCORER: errors.append('scorer_hash')
errors += validate(d)
corrupt={}
for name,fn in {
 'change_inode': lambda m: m['rows'][1]['after_external_inplace']['file'].__setitem__('ino',m['rows'][1]['precheck']['file']['ino']+1),
 'erase_prompt': lambda m: m['rows'][1]['after_optional_format_confirm'].__setitem__('modal_names',[]),
 'wrong_cells': lambda m: m['rows'][1]['score']['cells'].__setitem__('A1','office'),
 'bad_release': lambda m: m['rows'][0]['release'].__setitem__('verified',False),
}.items():
    m=copy.deepcopy(d); fn(m); corrupt[name]=bool(validate(m))
out={'schema':'agent-interface/libreoffice-save-conflict-inplace-audit-v1','allocation':'c254-pair-03','errors':errors,'pass':not errors,'corruption_rejections':corrupt,'corruption_pass':all(corrupt.values()),'runner_sha256':sha(ROOT/'pair_runner_inplace.py'),'scorer_sha256':sha(ROOT/'score_any.py')}
(ROOT/'scored-pair-03'/'AUDIT.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2)); raise SystemExit(0 if out['pass'] and out['corruption_pass'] else 1)
