"""Foreground-bounded experiment supervision; no changes to experimental code."""
import json,subprocess,sys,time
from pathlib import Path
root=Path(__file__).resolve().parent
allocation=sys.argv[1]
dedup=sys.argv[2:]
with (root/f'{allocation}.stdout').open('w') as out, (root/f'{allocation}.stderr').open('w') as err:
    try:
        p=subprocess.run([sys.executable,str(root/'experiment.py'),'run',str(root/'results'/allocation),*dedup],stdout=out,stderr=err,timeout=240)
        result={'experiment_exit':p.returncode}
        if p.returncode==0:
            with (root/f'{allocation}.audit.stdout').open('w') as ao,(root/f'{allocation}.audit.stderr').open('w') as ae:
                a=subprocess.run([sys.executable,str(root/'audit.py'),str(root/'results'/allocation)],stdout=ao,stderr=ae,timeout=30)
                result['audit_exit']=a.returncode
    except BaseException as exc:
        result={'supervisor_error':repr(exc)}
(root/f'{allocation}.supervisor.json').write_text(json.dumps(result,indent=2)+'\n')
