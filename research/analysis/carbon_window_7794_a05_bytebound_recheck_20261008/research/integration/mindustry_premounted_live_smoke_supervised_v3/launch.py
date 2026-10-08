#!/usr/bin/env python3
"""Wait for exactly one frozen child command and retain its terminal receipt."""
import argparse, hashlib, json, os, subprocess, time
from pathlib import Path

def sha(path: Path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
    return h.hexdigest()

def dump_atomic(path: Path, obj):
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    os.replace(tmp,path)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--command-json',type=Path,required=True)
    a=ap.parse_args();root=a.root.resolve(); cmd_obj=json.loads(a.command_json.read_text(encoding='utf-8'))
    cmd=cmd_obj['command']; started=time.monotonic_ns()
    out=(root/'child.stdout.txt').open('w',encoding='utf-8');err=(root/'child.stderr.txt').open('w',encoding='utf-8')
    p=subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=out,stderr=err,close_fds=True)
    receipt={'schema':'mindustry-4457-launch-v1','launcher_pid':os.getpid(),'launcher_sid':os.getsid(0),'child_pid':p.pid,'command':cmd,'command_sha256':sha(a.command_json),'started_ns':started}
    dump_atomic(root/'LAUNCH_STARTED.json',receipt)
    rc=p.wait(); out.close();err.close();receipt['returncode']=rc;receipt['finished_ns']=time.monotonic_ns();receipt['result_exists']=Path(cmd_obj['expected_result']).is_file()
    if receipt['result_exists']:receipt['result_sha256']=sha(Path(cmd_obj['expected_result']))
    dump_atomic(root/'EXECUTION.json',receipt)
    return 0
if __name__=='__main__':raise SystemExit(main())
