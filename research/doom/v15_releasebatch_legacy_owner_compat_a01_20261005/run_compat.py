"""Materialize pinned source blobs and execute the isolated owner-protocol check."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
p=Path(__file__).resolve().parent
def main():
 a=argparse.ArgumentParser();a.add_argument('output',type=Path);args=a.parse_args();manifest=json.loads((p/'source-manifest.json').read_text());src=(args.output/'source').resolve();args.output.mkdir(parents=True,exist_ok=False)
 for rel,r in manifest['files'].items():
  data=(p/'source-snapshots'/(rel+'.txt')).read_bytes()
  if len(data)!=r['bytes'] or hashlib.sha256(data).hexdigest()!=r['sha256']:raise ValueError('frozen source mismatch: '+rel)
  target=src/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
 command=[sys.executable,'-B',str(p/'probe_compat.py'),str(src),str((args.output/'result.json').resolve())]
 result=subprocess.run(command,capture_output=True,timeout=15)
 (args.output/'stdout.txt').write_bytes(result.stdout);(args.output/'stderr.txt').write_bytes(result.stderr)
 (args.output/'exit.json').write_text(json.dumps({'command':command,'exit_code':result.returncode},indent=2)+'\n')
 return result.returncode
if __name__=='__main__':raise SystemExit(main())
