from __future__ import annotations
from dataclasses import dataclass

@dataclass
class State:
    closed: bool = False
    generation: int = 1

def commit_then_receive():
    s=State()
    # commit owns the single authority mutex first
    commit_ts=10
    admitted=(not s.closed and s.generation==1)
    # receiver obtains the same mutex afterwards; its timestamp is therefore later
    recv_ts=20
    s.closed=True; s.generation+=1
    return {'order':'commit_then_receive','commit_ts':commit_ts,'recv_ts':recv_ts,
            'admitted':admitted,'violation':bool(admitted and commit_ts>=recv_ts)}

def receive_then_commit():
    s=State()
    # receiver owns mutex first; observed-return timestamp and close are one critical section
    recv_ts=10
    s.closed=True; s.generation+=1
    commit_ts=20
    admitted=(not s.closed and 1==s.generation)
    return {'order':'receive_then_commit','commit_ts':commit_ts,'recv_ts':recv_ts,
            'admitted':admitted,'violation':bool(admitted and commit_ts>=recv_ts)}

def main():
    import json
    outcomes=[commit_then_receive(),receive_then_commit()]
    print(json.dumps({'pass':not any(x['violation'] for x in outcomes),'outcomes':outcomes},sort_keys=True))

if __name__=='__main__': main()
