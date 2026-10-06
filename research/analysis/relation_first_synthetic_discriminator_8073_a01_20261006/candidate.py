import json,sys
from pathlib import Path

def jaccard(a,b):
    a,b=set(a),set(b)
    return len(a&b)/len(a|b) if a|b else 0.0

def rank(target,sources,mode):
    key='keywords' if mode=='keyword_first' else 'relations'
    rows=[]
    for s in sources:
        score=jaccard(target[key],s[key])
        rows.append((score,s['id']))
    rows.sort(key=lambda x:(-x[0],x[1]))
    return [sid for _,sid in rows[:3]]

def main(inp,out):
    data=json.loads(Path(inp).read_text())
    smap={s['id']:s for s in data['sources']}
    rows=[]
    for t in data['targets']:
        rec={'target':t['id']}
        for mode in ('keyword_first','relation_first'):
            top=rank(t,data['sources'],mode)
            valid=sum(t['id'] in smap[x]['valid_for'] for x in top)
            decoys=sum(smap[x]['kind']=='highlex_lowrel' for x in top)
            positives=sum(smap[x]['kind']=='lowlex_highrel' and t['id'] in smap[x]['valid_for'] for x in top)
            rec[mode]={'top3':top,'valid':valid,'decoys':decoys,'seeded_positive':positives}
        rows.append(rec)
    totals={m:{'valid':sum(r[m]['valid'] for r in rows),'decoys':sum(r[m]['decoys'] for r in rows),'seeded_positive':sum(r[m]['seeded_positive'] for r in rows)} for m in ('keyword_first','relation_first')}
    result={'schema':'relation-first-synthetic-result-v1','rows':rows,'totals':totals,'authority':False,'claim_scope':'synthetic retrieval discriminator only'}
    Path(out).write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
if __name__=='__main__': main(sys.argv[1],sys.argv[2])
