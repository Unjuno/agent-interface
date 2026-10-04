"""Bounded saved-workbook predicate evidence; not proof of action causation."""
import hashlib,io,time
from pathlib import Path
from openpyxl import load_workbook


def inspect_saved_cells(path, *, action_id, expected, observation_closed):
    if not isinstance(action_id,str) or not action_id:raise ValueError('action_id required')
    if type(observation_closed)is not bool:raise ValueError('explicit observation boundary required')
    if not isinstance(expected,dict) or not expected:raise ValueError('nonempty cell contract required')
    for address,value in expected.items():
        if not isinstance(address,str) or not address or type(value) not in (int,float,str,type(None)):
            raise ValueError('scalar cell contract required')
    result=dict(event='effect_evidence',action_id=action_id,status='UNKNOWN',
                scope='saved first worksheet cells at one sample',
                attribution='not_established',authority='none',
                expected=dict(expected),observation_closed=observation_closed,
                started_ns=time.perf_counter_ns())
    try:
        # Parse exactly the bytes whose digest is reported; no second file read.
        data=Path(path).read_bytes();result['sampled_ns']=time.perf_counter_ns()
        result['artifact_sha256']=hashlib.sha256(data).hexdigest()
        wb=load_workbook(io.BytesIO(data),read_only=True,data_only=False)
        try:
            sheet=wb.worksheets[0];actual={address:sheet[address].value for address in expected}
            formulas=[address for address in expected if sheet[address].data_type=='f']
        finally:wb.close()
        result['actual']=actual
        if formulas:result.update(reason='formula_evaluation_unavailable',formula_cells=formulas)
        elif actual==expected:result.update(status='VERIFIED',reason='sample_matches_declared_cells')
        elif observation_closed:result.update(status='CONTRADICTED',reason='sample_mismatch_at_closed_boundary')
        else:result.update(reason='sample_mismatch_window_open')
    except Exception as exc:
        result.update(reason='evidence_unavailable',error=dict(type=type(exc).__name__,message=str(exc)))
    result['finished_ns']=time.perf_counter_ns()
    return result
