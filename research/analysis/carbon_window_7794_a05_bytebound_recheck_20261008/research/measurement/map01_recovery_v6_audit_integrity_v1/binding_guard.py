from __future__ import annotations
import json
from pathlib import Path

PAIRS=(1,2,3)

def _load(path:Path)->dict:
    v=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(v,dict): raise ValueError(f'expected object: {path}')
    return v

def binding_failures(root:Path)->list[str]:
    root=Path(root); summary=_load(root/'summary.json'); pairs=summary.get('pairs')
    if not isinstance(pairs,list): return ['summary:pairs']
    by_index={p.get('pair_index'):p for p in pairs if isinstance(p,dict)}
    failures=[]
    for i in PAIRS:
        pair=by_index.get(i)
        if not isinstance(pair,dict): failures.append(f'pair{i}:summary_missing'); continue
        for arm,field in (
            ('coast_control','coast_no_retained_input_upper_ns'),
            ('bounded_recovery','recovery_no_retained_input_upper_ns')):
            arm_summary=_load(root/f'pair-{i:02d}'/arm/'arm-summary.json')
            bounds=arm_summary.get('input_bounds') or {}
            observed=bounds.get('no_retained_input_upper_bound_ns')
            declared=pair.get(field)
            if type(observed) is not int or type(declared) is not int or observed!=declared:
                failures.append(f'pair{i}:{arm}:{field}:summary_arm_mismatch')
    return failures
