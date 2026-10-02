#!/usr/bin/env python3
"""One-shot detached launcher; returns after durable spawn receipt."""
import argparse, hashlib, json, os, subprocess
from pathlib import Path

def sha(path: Path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--command-json',type=Path,required=True);ap.add_argument('--launch',type=Path,required=True)
 a=ap.parse_args();root=a.root.resolve();root.mkdir(parents=True,exist_ok=False)
 marker=root/'SPAWN.json'
 supout=(root/'supervisor.stdout.txt').open('w',encoding='utf-8');superr=(root/'supervisor.stderr.txt').open('w',encoding='utf-8')
 cmd=[os.environ.get('PYTHON','python3'),str(a.launch.resolve()),'--root',str(root),'--command-json',str(a.command_json.resolve())]
 p=subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=supout,stderr=superr,start_new_session=True,close_fds=True)
 rec={'schema':'mindustry-4457-spawn-v1','spawn_pid':p.pid,'spawn_sid':os.getsid(p.pid),'spawn_pgid':os.getpgid(p.pid),'command':cmd,'launch_sha256':sha(a.launch.resolve()),'command_sha256':sha(a.command_json.resolve())}
 marker.write_text(json.dumps(rec,indent=2,sort_keys=True)+'\n',encoding='utf-8')
 print(json.dumps(rec,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
