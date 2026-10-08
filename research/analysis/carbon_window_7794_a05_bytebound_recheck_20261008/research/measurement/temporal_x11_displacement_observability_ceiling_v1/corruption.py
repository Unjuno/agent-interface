from __future__ import annotations
import argparse,copy,json,os,tempfile
from audit import audit

def w(obj):
    fd,p=tempfile.mkstemp(suffix='.json');os.close(fd);open(p,'w').write(json.dumps(obj,separators=(',',':'),sort_keys=True));return p

def main():
    ap=argparse.ArgumentParser();ap.add_argument('formal');ap.add_argument('out');a=ap.parse_args();base=json.load(open(a.formal));tests=[];m=[]
    x=copy.deepcopy(base);x['bound']=0.5;m.append(('bound',x))
    x=copy.deepcopy(base);x['boundary_rows'][0]['phase_ms']=0;m.append(('phase',x))
    x=copy.deepcopy(base);x['by_age']['100']['published_correct']=189;m.append(('correct_count',x))
    x=copy.deepcopy(base);x['pattern_checks']['100'][0]['pair']=[5.0,5.0];m.append(('pattern',x))
    x=copy.deepcopy(base);x['boundary_rows'].pop();m.append(('row_count',x))
    for name,obj in m:
        p=w(obj)
        try:
            r=audit(p,True);tests.append({'name':name,'rejected':r['decision']=='FAIL_INTEGRITY','decision':r['decision'],'errors':r['errors']})
        finally:os.unlink(p)
    out={'all_rejected':all(t['rejected'] for t in tests),'tests':tests};open(a.out,'w').write(json.dumps(out,separators=(',',':'),sort_keys=True));print(json.dumps(out,sort_keys=True))
if __name__=='__main__':main()
