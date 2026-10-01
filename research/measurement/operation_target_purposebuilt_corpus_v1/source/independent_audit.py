import json,hashlib,sys
from collections import defaultdict
from schema import VISIBLE_KEYS,FORBIDDEN_VISIBLE_KEYS,disp_key

# Separate oracle formulation, intentionally does not import oracle.py/generator.py/validator.py.
def expected(f):
    if f['hard_invalid']: return [{'op':'YIELD','reason':'STALE_STATE'}]
    if f['unsupported_operation']: return [{'op':'YIELD','reason':'UNSUPPORTED_OPERATION'}]
    if f['required_payload'] and not f['payload_available']: return [{'op':'YIELD','reason':'PAYLOAD_MISSING'}]
    if f['semantic_no_action']: return [{'op':'NO_LOCAL_ACTION','reason':'ALREADY_SATISFIED'}]
    valid=[t for t in f['targets'] if t['present'] and t['compatible']]
    if f['requires_target'] and not valid:return [{'op':'YIELD','reason':'MISSING_TARGET'}]
    if f['ambiguous']:return [{'op':'YIELD','reason':'AMBIGUOUS_TARGET'}]
    if f['operation']=='TYPE_TEXT':return [{'op':'TYPE_TEXT','target':valid[0]['id'],'payload_ref':f['payload_ref']}]
    return [{'op':f['operation'],'target':t['id']} for t in valid if t['acceptable']]

def main(corpus='CORPUS.json',result='RESULT.json'):
    rows=json.load(open(corpus)); res=json.load(open(result)); errors=[]; signatures=defaultdict(set); units=defaultdict(set)
    pos=neg=noa=yld=alts=0; ops=set()
    for r in rows:
        p=r['candidate_input']; units[r['split']].add(r['scenario_unit_id'])
        if set(p)!=VISIBLE_KEYS or set(p)&FORBIDDEN_VISIBLE_KEYS:errors.append([r['row_id'],'visible_leak'])
        ex=expected(r['oracle_facts']); a=r['acceptable']
        if sorted(map(disp_key,ex))!=sorted(map(disp_key,a)):errors.append([r['row_id'],'oracle'])
        ee=[d for d in ex if d['op'] in ('CLICK','TYPE_TEXT','SCROLL')]
        if ee:pos+=1;ops.update(d['op'] for d in ee)
        else:neg+=1
        noa+=any(d['op']=='NO_LOCAL_ACTION' for d in ex); yld+=any(d['op']=='YIELD' for d in ex); alts+=len(ee)>=2
        signatures[json.dumps(p,sort_keys=True,separators=(',',':'))].add(tuple(sorted(disp_key(d) for d in ex)))
    alias=sum(len(v)>1 for v in signatures.values())
    if units['train'] & units['eval']:errors.append(['corpus','split'])
    if alias:errors.append(['corpus','alias',alias])
    digest=hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    if digest!=res['corpus_digest_sha256']:errors.append(['corpus','digest'])
    if (len(rows),len(units['train']|units['eval']),pos,neg,noa,yld,alts)!=(96,12,48,48,12,36,24):errors.append(['corpus','counts'])
    if len(ops)<2:errors.append(['corpus','ops'])
    if res['primary_invocations']!=1 or res['reruns']!=0:errors.append(['result','invocation'])
    if res['model_calls'] or res['gui_actions'] or res['task_input_actions']:errors.append(['result','actions'])
    if res['decision']!='READY_PURPOSEBUILT_OPERATION_TARGET_CORPUS_SCOPED':errors.append(['result','decision'])
    out={'pass':not errors,'errors':errors,'independent_digest_sha256':digest,'rows':len(rows),'scenario_units':len(units['train']|units['eval']),'positives':pos,'semantic_negatives':neg,'no_local_action':noa,'yield':yld,'target_alternative_rows':alts,'alias_groups':alias,'operation_families':sorted(ops)}
    print(json.dumps(out,sort_keys=True)); sys.exit(bool(errors))
if __name__=='__main__':main(*sys.argv[1:])
