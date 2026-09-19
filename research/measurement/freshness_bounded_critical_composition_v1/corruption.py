import copy,json,tempfile,os
from audit import verify

def main(path):
    with open(path) as f: base=json.load(f)
    muts=[]
    for name,fn in [
      ('seed',lambda x:x.__setitem__('seed',x['seed']+1)),
      ('digest',lambda x:x.__setitem__('digest','0'*64)),
      ('critical',lambda x:x.__setitem__('critical_records',x['critical_records']+1)),
      ('decision',lambda x:x.__setitem__('decision','PASS_BOGUS')),
      ('invocation',lambda x:x.__setitem__('formal_invocations',2)),
    ]:
        x=copy.deepcopy(base); fn(x)
        fd,p=tempfile.mkstemp(suffix='.json'); os.close(fd)
        with open(p,'w') as f: json.dump(x,f)
        errs=verify(p); os.unlink(p)
        if not errs: raise AssertionError(name)
        muts.append([name,errs])
    print(json.dumps({'corruptions_rejected':len(muts),'details':muts},sort_keys=True))
if __name__=='__main__':
    import sys; main(sys.argv[1])
