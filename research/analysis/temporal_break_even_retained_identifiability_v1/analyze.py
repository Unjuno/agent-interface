import argparse,hashlib,json
from pathlib import Path
REQ=('actual_model_usage','fixed_11_equivalent_presentation','query_conditioned_model_return','continuation_overhead_measured','matched_task_source_model_session_cache','independent_correctness_value_endpoint')
EXPECTED_BLOBS={
'sheet_report':'60f81388f904fd0dc86d92611569b13c8300a6e2','sheet_ledger':'5ff1984a63894df69efb14cdb21b0b57963f6951','ring_latency':'55262736441638220c11931442450e6025147e2b','matched_selection':'c72111db0ed06622cb035446ac68dbede49bccc7','cost_contract':'a20e519544b1efb310efe8c973333eb7fdfa2044','map01_temporal_model':'d2fbcbc199c3ea45965bdb85f2193bf6017eff05','ring_plan':'9fb34104f5044082f69c35287e965b3dd69a314c'}
SEARCHES=('query_temporal_observation','MODEL_QUERYABLE_HISTORY','temporal_sheet_matched_prediction_v1','READY_FOR_MODEL_ALLOCATION temporal')
def admissible(row): return all(row.get(k) is True for k in REQ)
def decide(ledger,smap):
    fam=ledger['families']; adm=[r['id'] for r in fam if admissible(r)]
    model=sum(r.get('actual_model_usage') is True for r in fam)
    local=sum(r.get('local_query_latency_measured') is True for r in fam)
    search=smap['bounded_default_branch_searches']; qhits=sum(search[q]['result_count'] for q in SEARCHES[:2])
    source_ok=all(smap['sources'][k]['git_blob']==v for k,v in EXPECTED_BLOBS.items())
    forbidden_ok=ledger.get('causal_cost_estimate') is None and len(ledger.get('forbidden_inferences',[]))>=4
    good=len(fam)>=5 and model>=1 and local>=1 and len(adm)==0 and qhits==0 and source_ok and forbidden_ok
    return {'decision':'PASS_RETAINED_TEMPORAL_BREAK_EVEN_NOT_IDENTIFIABLE_SCOPED' if good else 'FAIL_INTEGRITY','family_count':len(fam),'actual_model_family_count':model,'local_query_latency_family_count':local,'admissible_rows':adm,'bounded_model_query_search_hits':qhits,'source_map_exact':source_ok,'causal_estimate_emitted':ledger.get('causal_cost_estimate') is not None}
def corruptions(ledger,smap):
    base=decide(ledger,smap)['decision']
    # 1 local latency laundered into model H: still must not become admissible because no model usage/query return/fixed11.
    x=json.loads(json.dumps(ledger)); r=next(z for z in x['families'] if z['id']=='queryable_ring_latency'); r['continuation_overhead_measured']=True
    c1=(decide(x,smap)['admissible_rows']==[])
    # 2 four-source packed sheet relabelled fixed11: still lacks query/H/matchedness.
    x=json.loads(json.dumps(ledger)); r=next(z for z in x['families'] if z['id']=='map01_packed_temporal_model'); r['fixed_11_equivalent_presentation']=True
    c2=(decide(x,smap)['admissible_rows']==[])
    # 3 fabricated fully matched queryable row must destroy the non-identifiability decision.
    x=json.loads(json.dumps(ledger)); fake={'id':'fabricated','source':'cost_contract','kind':'fake'}; fake.update({k:True for k in REQ}); x['families'].append(fake)
    c3=(decide(x,smap)['decision']!='PASS_RETAINED_TEMPORAL_BREAK_EVEN_NOT_IDENTIFIABLE_SCOPED')
    # 4 causal estimate laundering must fail.
    x=json.loads(json.dumps(ledger)); x['causal_cost_estimate']={'tokens_saved':7}
    c4=(decide(x,smap)['decision']!='PASS_RETAINED_TEMPORAL_BREAK_EVEN_NOT_IDENTIFIABLE_SCOPED')
    return {'local_H_laundering_rejected':c1,'packed4_as_fixed11_rejected':c2,'fabricated_matched_row_detected':c3,'causal_estimate_laundering_rejected':c4,'base_pass':base=='PASS_RETAINED_TEMPORAL_BREAK_EVEN_NOT_IDENTIFIABLE_SCOPED'}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--ledger',required=True);ap.add_argument('--source-map',required=True);ap.add_argument('--construction',action='store_true');ap.add_argument('--output',required=True);a=ap.parse_args();out=Path(a.output);assert not out.exists();ledger=json.loads(Path(a.ledger).read_text());smap=json.loads(Path(a.source_map).read_text());r=decide(ledger,smap);r['corruption_controls']=corruptions(ledger,smap);r['formal_invocations']=0 if a.construction else 1;r['reruns']=0;r['replacements']=0;r['tuning']=0
    if not all(r['corruption_controls'].values()):r['decision']='FAIL_INTEGRITY'
    if a.construction and r['decision'].startswith('PASS_'):r['decision']='CONSTRUCTION_PASS'
    raw=json.dumps(r,sort_keys=True,separators=(',',':')).encode();r['digest']=hashlib.sha256(raw).hexdigest();out.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(r,indent=2,sort_keys=True))
if __name__=='__main__':main()
