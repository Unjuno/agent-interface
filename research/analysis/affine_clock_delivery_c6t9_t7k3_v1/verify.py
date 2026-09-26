"""Read-only retained-evidence check; never run the consumed corpus runner."""
from __future__ import annotations
import argparse,json,subprocess,sys,tempfile
from pathlib import Path
from unpack import restore

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--control',type=int,choices=range(12))
    args=parser.parse_args()
    here=Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory(prefix='c6t9-review-') as tmp:
        root=Path(tmp)/'original'
        reconstruction=restore(here,root)
        # Human-readable copies must be exactly the corresponding retained bytes.
        copies=[]
        for p in (here/'original').rglob('*'):
            if p.is_file():
                name=p.relative_to(here/'original')
                if p.read_bytes()!=(root/name).read_bytes():
                    raise ValueError('readable source mismatch: '+str(name))
                copies.append(str(name))
        argv=[sys.executable,'-B','verify_readonly.py']
        if args.control is not None:argv+=['--control',str(args.control)]
        p=subprocess.run(argv,cwd=root,capture_output=True,timeout=35)
        if p.returncode or p.stderr:
            raise RuntimeError(f'retained verifier failed: exit={p.returncode}; {p.stderr.decode()}')
        print(json.dumps({'restoration':reconstruction,'readable_copies':len(copies),
                          'retained_check':json.loads(p.stdout),'new_scientific_runs':0},sort_keys=True,indent=2))
    return 0

if __name__=='__main__':raise SystemExit(main())
