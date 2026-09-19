"""Retry conflict, uncertain write and concurrent same-ID controls."""
import json,threading
from pathlib import Path
from command_once import CommandOnce
calls=[];sender=CommandOnce(calls.append,capacity=1);command=dict(op='clock')
a=sender.send('one',command);b=sender.send('one',dict(command))
assert len(calls)==1 and not a['replayed'] and b['replayed']
for identifier,payload in [('one',dict(op='finish')),('two',command)]:
    try:sender.send(identifier,payload)
    except ValueError:pass
    else:raise AssertionError('conflict or overflow accepted')
attempts=[]
def uncertain(line):attempts.append(line);raise OSError('failure after possible write')
s=CommandOnce(uncertain);first=s.send('uncertain',command);retry=s.send('uncertain',command)
assert first['state']==retry['state']=='write_uncertain' and len(attempts)==1
parallel=[];s=CommandOnce(parallel.append)
threads=[threading.Thread(target=s.send,args=('shared',command)) for _ in range(8)]
for t in threads:t.start()
for t in threads:t.join()
assert len(parallel)==1
report=dict(same_id_writes=len(calls),uncertain_write_attempts=len(attempts),concurrent_same_id_writes=len(parallel),conflict_and_capacity_rejected=True,
            scope='one process lifetime; write attempt only, not application exactly-once')
out=Path(__file__).resolve().parent/'results/command-once-01.json';assert not out.exists();out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
