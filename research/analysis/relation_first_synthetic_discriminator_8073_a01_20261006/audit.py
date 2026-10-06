import json,sys,hashlib
from pathlib import Path

def jac(a,b):
    a,b=set(a),set(b); return len(a&b)/len(a|b) if a|b else 0.0

def expected(t,sources,key):
    scored=sorted(((jac(t[key],s[key]),s['id']) for s in sources),key=lambda x:(-x[0],x[1]))
    return [sid for _,sid in scored[:3]]

def main(corpus_p,result_p,out_p):
    data=json.loads(Path(corpus_p).read_text()); result=json.loads(Path(result_p).read_text())
    smap={s['id']:s for s in data['sources']}; tmap={t['id']:t for t in data['targets']}
    errors=[]; checks=0
    if len(result.get('rows',[]))!=8: errors.append('row_count');
    checks+=1
    for r in result.get('rows',[]):
        t=tmap.get(r.get('target')); checks+=1
        if not t: errors.append('unknown_target'); continue
        for mode,key in [('keyword_first','keywords'),('relation_first','relations')]:
            exp=expected(t,data['sources'],key); checks+=1
            if r[mode]['top3']!=exp: errors.append(f"{t['id']}:{mode}:rank")
            valid=sum(t['id'] in smap[x]['valid_for'] for x in exp); checks+=1
            if r[mode]['valid']!=valid: errors.append(f"{t['id']}:{mode}:valid")
            dec=sum(smap[x]['kind']=='highlex_lowrel' for x in exp); checks+=1
            if r[mode]['decoys']!=dec: errors.append(f"{t['id']}:{mode}:decoy")
            pos=sum(smap[x]['kind']=='lowlex_highrel' and t['id'] in smap[x]['valid_for'] for x in exp); checks+=1
            if r[mode]['seeded_positive']!=pos: errors.append(f"{t['id']}:{mode}:pos")
    kt=result['totals']['keyword_first']; rt=result['totals']['relation_first']; checks+=5
    if rt['seeded_positive']!=8: errors.append('relation_positive_denominator')
    if kt['seeded_positive']!=0: errors.append('keyword_positive_expected0')
    if rt['valid']<=kt['valid']: errors.append('no_valid_discriminator')
    if rt['decoys']>=kt['decoys']: errors.append('no_decoy_discriminator')
    if result.get('authority') is not False: errors.append('authority')
    audit={'status':'PASS_SYNTHETIC_RETRIEVAL_DISCRIMINATOR_SCOPED' if not errors else 'FAIL_AUDIT','checks':checks,'errors':errors,'corpus_sha256':hashlib.sha256(Path(corpus_p).read_bytes()).hexdigest(),'result_sha256':hashlib.sha256(Path(result_p).read_bytes()).hexdigest()}
    Path(out_p).write_text(json.dumps(audit,sort_keys=True,indent=2)+'\n')
    raise SystemExit(0 if not errors else 1)
if __name__=='__main__': main(*sys.argv[1:4])
