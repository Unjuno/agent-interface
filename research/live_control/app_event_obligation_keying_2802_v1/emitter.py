from __future__ import annotations
import json,os,sys,time
from pathlib import Path
SCENARIOS={
 'BOTH_COMPLETE':[('A','o1'),('A','o2'),('B','o1'),('B','o2')],
 'CROSS_ONLY':[('A','o1'),('B','o2')],
 'WRONG_B_THEN_RIGHT':[('A','o1'),('B','o2'),('B','o1')],
 'O2_COMPLETE_ONLY':[('A','o2'),('B','o2')],
 'INTERLEAVED_COMPLETE':[('A','o1'),('A','o2'),('B','o2'),('B','o1')],
 'MISSING_ID':[('A','o1'),('B',None)],
}

def main():
    cfg=json.loads(sys.stdin.readline()); s=cfg['scenario']; path=Path(cfg['state_path'])
    state={'o1':'READY','o2':'READY'}; path.write_text(json.dumps(state,sort_keys=True))
    logical_tick=cfg['logical_tick']
    for seq,(label,oid) in enumerate(SCENARIOS[s],1):
        if label=='B' and oid in state:
            state[oid]='DONE'; path.write_text(json.dumps(state,sort_keys=True))
        row={'source_id':'app','clock_domain':'APP_LOGICAL_TICK','tick':logical_tick,'arrival_ns':time.monotonic_ns(),'seq':seq,'obligation_id':oid,'label':label,'pid':os.getpid()}
        print(json.dumps(row,sort_keys=True),flush=True)
        time.sleep(0.001)
if __name__=='__main__': main()
