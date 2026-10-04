from pathlib import Path
import subprocess,sys,json
from controller_process_cleanup import retire_process
out=Path(__file__).resolve().parent/'process-cleanup-01';out.mkdir(exist_ok=False)
p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
r=retire_process(p,grace_seconds=.1);p.stdout.close();p.stderr.close();r['scope']='owned sleeping Python process only; no container/model/game, not physical input release';(out/'RESULT.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r));assert r['terminal']
