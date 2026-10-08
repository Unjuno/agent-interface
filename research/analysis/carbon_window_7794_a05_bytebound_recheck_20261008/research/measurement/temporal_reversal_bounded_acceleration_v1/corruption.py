import argparse,copy,json,tempfile,os
from audit import audit
ap=argparse.ArgumentParser(); ap.add_argument('formal'); ap.add_argument('out'); a=ap.parse_args(); base=json.load(open(a.formal)); muts=[]
for name,fn in [
 ('accel',lambda x:x['rows'][0].__setitem__('accel_ppm_per_100ms',123)),
 ('jitter',lambda x:x['rows'][0]['jitter_u'].__setitem__(0,x['rows'][0]['jitter_u'][0]+1)),
 ('oracle',lambda x:x['rows'][0].__setitem__('oracle',-x['rows'][0]['oracle'])),
 ('count',lambda x:(x['rows'].pop(),x.__setitem__('row_count',x['row_count']-1))),
 ('authority',lambda x:x['rows'][0].__setitem__('authority_granted',True))]:
    y=copy.deepcopy(base); fn(y); muts.append((name,y))
tests=[]
for name,obj in muts:
    fd,p=tempfile.mkstemp(); os.close(fd); json.dump(obj,open(p,'w'),separators=(',',':'),sort_keys=True)
    try:r=audit(p,True); tests.append({'name':name,'rejected':r['decision']=='FAIL_INTEGRITY','errors':r['errors']})
    finally:os.unlink(p)
out={'all_rejected':all(t['rejected'] for t in tests),'tests':tests}; json.dump(out,open(a.out,'w'),indent=2,sort_keys=True); print(json.dumps(out,sort_keys=True))
