import json,os,signal,sys,time
from pathlib import Path
p=Path(sys.argv[1])
rows=json.loads((p/'processes.json').read_text())
def current(row):
    try:
        text=Path(f"/proc/{row['pid']}/stat").read_text()
        parts=text[text.rfind(')')+2:].split()
        if parts[19]!=row['starttime']: return 'replaced'
        return parts[0]
    except FileNotFoundError:
        return 'absent'
for row in reversed(rows):
    row['before_cleanup']=current(row)
    if row['before_cleanup'] not in ('absent','replaced','Z','X','x'):
        os.kill(row['pid'],signal.SIGTERM)
    for _ in range(100):
        state=current(row)
        if state in ('absent','replaced','Z','X','x'): break
        time.sleep(.01)
    else:
        raise RuntimeError('process did not terminate; inspect same identity')
    row['after_cleanup']=state
(p/'external-cleanup.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps(rows,indent=2))
