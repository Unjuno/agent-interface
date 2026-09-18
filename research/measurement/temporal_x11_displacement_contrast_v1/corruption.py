from __future__ import annotations
import argparse,copy,json,os,tempfile
from audit import audit

def tmp(obj):
    fd,p=tempfile.mkstemp(suffix='.json');os.close(fd)
    with open(p,'w') as f:json.dump(obj,f,separators=(',',':'),sort_keys=True)
    return p

def main():
    ap=argparse.ArgumentParser();ap.add_argument('formal');ap.add_argument('out');a=ap.parse_args();base=json.load(open(a.formal)); tests=[]; muts=[]
    x=copy.deepcopy(base); x['pairs_rows'][0]['frames'][0]['scanline_b64']='AAAA'+x['pairs_rows'][0]['frames'][0]['scanline_b64'][4:]; muts.append(('scanline',x))
    x=copy.deepcopy(base); x['pairs_rows'][0]['red']=17; muts.append(('color_arm',x))
    x=copy.deepcopy(base); x['pairs_rows'][0]['frames'][0]['authored_root_x']+=1; muts.append(('authored_center',x))
    x=copy.deepcopy(base); x['pairs_rows'].pop(); x['summary']['pairs']-=1; muts.append(('row_count',x))
    for name,obj in muts:
        p=tmp(obj)
        try:
            r=audit(p,True); rejected=bool(r['errors']) or bool(r['science_gates']); tests.append({'name':name,'rejected':rejected,'errors':r['errors'],'science_gates':r['science_gates']})
        finally:os.unlink(p)
    out={'all_rejected':all(t['rejected'] for t in tests),'tests':tests};open(a.out,'w').write(json.dumps(out,separators=(',',':'),sort_keys=True));print(json.dumps(out,sort_keys=True))
if __name__=='__main__':main()
