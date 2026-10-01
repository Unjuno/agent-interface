from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys
from dataclasses import asdict
from pathlib import Path

EXPECTED_REDUCER_SHA256 = 'db0a9dfe31aa406dc0ceea2c13552be974226281eb0a33413bffe104e8b7e548'
PHASE_LEGACY_MAP = {
    'PUBLISHED_VERIFIED': 'PUBLISHED_VERIFIED',
    'REJECTED_PRE_EFFECT': 'REJECTED_PRE_EFFECT',
    'EFFECT_VERIFIED': 'EFFECT_VERIFIED',
    'EFFECT_CONTRADICTED': 'EFFECT_CONTRADICTED_UNCOMPENSATED',
}

def sha256(path: Path) -> str:
    h=hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()

def load_reducer(path: Path):
    actual=sha256(path)
    if actual != EXPECTED_REDUCER_SHA256:
        raise RuntimeError(f'reducer identity mismatch: {actual}')
    spec=importlib.util.spec_from_file_location('retained_effect_outcome_reducer', path)
    if spec is None or spec.loader is None: raise RuntimeError('cannot load reducer')
    mod=importlib.util.module_from_spec(spec); sys.modules[spec.name]=mod; spec.loader.exec_module(mod); return mod

def phase_input(mod, row: dict):
    op=mod.OperationKind(row['effect_class'])
    if row['phase_label']=='REJECTED_PRE_EFFECT':
        phase=mod.TerminalPhase.REJECTED_PRE_EFFECT; events=[]
    else:
        phase=mod.TerminalPhase.EFFECT_COMMITTED
        events=[mod.Event(1, mod.EventKind.EFFECT, row['effect_value'])]
    return dict(operation_kind=op, initial_state='old', intended_state='desired',
                current_state=row['effect_value'], terminal_phase=phase, events=events)

def comp_input(mod, row: dict):
    events=[mod.Event(int(e['seq']), mod.EventKind(e['kind']), e['value']) for e in row['events']]
    return dict(operation_kind=mod.OperationKind.DIRECT, initial_state=row['initial'],
                intended_state=row['intended'], current_state=row['final'],
                terminal_phase=mod.TerminalPhase.EFFECT_COMMITTED, events=events)

def serialize(outcome):
    d=asdict(outcome); d['kind']=outcome.kind.value; d['operation_kind']=outcome.operation_kind.value
    d['history']=[{'seq':e.seq,'kind':e.kind.value,'value':e.value} for e in outcome.history]
    return d

def run(reducer_path: Path, phase_path: Path, comp_path: Path):
    mod=load_reducer(reducer_path)
    prows=json.loads(phase_path.read_text()); crows=json.loads(comp_path.read_text()); rows=[]
    for row in prows:
        got=mod.reduce_outcome(**phase_input(mod,row)); expected=PHASE_LEGACY_MAP[row['phase_label']]
        rows.append({'cohort':'phase','id':row['id'],'source_label':row['phase_label'],
                     'expected_normalized':expected,'got':got.kind.value,
                     'match':got.kind.value==expected,'outcome':serialize(got)})
    for row in crows:
        got=mod.reduce_outcome(**comp_input(mod,row)); expected=row['phase_result']
        rows.append({'cohort':'compensation','id':row['id'],'source_label':row['phase_result'],
                     'expected_normalized':expected,'got':got.kind.value,
                     'match':got.kind.value==expected,'outcome':serialize(got)})
    return {'schema':'effect-outcome-retained-replay-v1','reducer_sha256':sha256(reducer_path),
            'phase_source_sha256':sha256(phase_path),'comp_source_sha256':sha256(comp_path),
            'rows':rows,'count':len(rows),'matched':sum(r['match'] for r in rows),
            'all_match':all(r['match'] for r in rows)}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('reducer',type=Path); ap.add_argument('phase',type=Path); ap.add_argument('comp',type=Path); ap.add_argument('out',type=Path)
    a=ap.parse_args(); a.out.write_text(json.dumps(run(a.reducer,a.phase,a.comp),indent=2,sort_keys=True)+'\n')
if __name__=='__main__': main()
