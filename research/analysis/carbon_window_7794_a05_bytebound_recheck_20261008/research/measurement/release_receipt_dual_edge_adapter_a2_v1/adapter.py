from __future__ import annotations
from dataclasses import asdict
from candidate_988 import Actuation

PINNED = {
    'input_owner_v11_git_blob': '842071284156d3ccc647f47135ee62a9e512cb56',
    'doom_typed_release_backend_v2_git_blob': 'cf13d630ae22a50272a766c86d7f325f352a89d7',
    'actuation_candidate_git_blob': '0482cf4c08b8c04d524a3eac11b798f07f0e0524',
}
LINEAGE = ('id','step','owner_id','intent_token')

def _int(v): return type(v) is int

def adapt(down: dict, up: dict, source_identity: dict) -> dict:
    def reject(reason):
        return {'accepted':False,'reason':reason,'grants_input_authority':False}
    if source_identity != PINNED: return reject('source_identity_drift')
    if not isinstance(down,dict) or not isinstance(up,dict): return reject('missing_evidence')
    if down.get('event')!='input_admission': return reject('unexpected_down_event')
    if up.get('event')!='input_release_rpc' or up.get('operation')!='up': return reject('unexpected_up_event_or_operation')
    if down.get('grants_input_authority',False) or up.get('grants_input_authority') is not False: return reject('authority_contradiction')
    if up.get('x11_release_and_sync_completed_before_return') is not True: return reject('release_completion_unproven')
    for k in LINEAGE:
        if k not in down or k not in up: return reject('missing_lineage')
        if down[k] != up[k]: return reject('lineage_mismatch')
    dk=down.get('key'); uk=up.get('payload')
    if not isinstance(dk,str) or not dk or dk!=uk: return reject('key_mismatch')
    for k in ('admitted_ns','input_ack_ns'):
        if not _int(down.get(k)): return reject('malformed_down_timestamp')
    for k in ('call_started_ns','call_returned_ns'):
        if not _int(up.get(k)): return reject('malformed_up_timestamp')
    dl,dh=down['admitted_ns'],down['input_ack_ns']; ul,uh=up['call_started_ns'],up['call_returned_ns']
    if not (0 <= dl <= dh <= ul <= uh): return reject('crossed_or_invalid_intervals')
    if up.get('release_transition_interval_ns') != [ul,uh]: return reject('release_interval_mismatch')
    if up.get('interval_width_ns') != uh-ul: return reject('release_width_mismatch')
    actuation_id=f"{down['id']}:{down['step']}:{down['owner_id']}:{down['intent_token']}:{dk}"
    act=Actuation(actuation_id,dl,dh,ul,uh,())
    return {
        'accepted':True,'reason':'accepted',
        'lineage':{**{k:down[k] for k in LINEAGE},'key':dk},
        'clock_provenance_disposition':'SOURCE_PINNED_SAME_PROCESS_PERF_COUNTER_NS',
        'physical_edge_exactness':'INTERVAL_CENSORED_BOTH_EDGES',
        'actuation':asdict(act),
        'grants_input_authority':False,
    }
