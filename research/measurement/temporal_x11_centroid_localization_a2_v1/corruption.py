from __future__ import annotations
import argparse, copy, json, pathlib, tempfile, os
from audit import audit

def temp(obj):
    fd,p=tempfile.mkstemp(suffix='.json'); os.close(fd); pathlib.Path(p).write_text(json.dumps(obj,separators=(',',':'),sort_keys=True)); return p

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('formal'); ap.add_argument('out'); a=ap.parse_args()
    base=json.loads(pathlib.Path(a.formal).read_text()); tests=[]
    muts=[]
    x=copy.deepcopy(base); s=x['pairs_rows'][0]['frames'][0]['scanline_b64']; x['pairs_rows'][0]['frames'][0]['scanline_b64']=('A' if s[0]!='A' else 'B')+s[1:]; muts.append(('scanline',x))
    x=copy.deepcopy(base); x['pairs_rows'][0]['frames'][0]['authored_root_x']+=1.0; muts.append(('authored_center',x))
    x=copy.deepcopy(base); x['pairs_rows'][0]['direction']*=-1; muts.append(('session_direction',x))
    x=copy.deepcopy(base); x['pairs_rows'].pop(); muts.append(('row_count',x))
    for name,obj in muts:
        p=temp(obj)
        try:
            r=audit(p,True); rejected=r['decision']=='FAIL_INTEGRITY' or bool(r['science_gates'])
            tests.append({'name':name,'rejected':rejected,'decision':r['decision'],'errors':r['errors'],'science_gates':r['science_gates']})
        except Exception as e:
            tests.append({'name':name,'rejected':True,'exception':repr(e)})
        finally: os.unlink(p)
    out={'all_rejected':all(t['rejected'] for t in tests),'tests':tests}
    pathlib.Path(a.out).write_text(json.dumps(out,separators=(',',':'),sort_keys=True)); print(json.dumps(out,sort_keys=True))
if __name__=='__main__':main()
