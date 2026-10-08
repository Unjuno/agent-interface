"""Exhaust every schema-v3 cover command combination through the v23 compiler."""
import itertools
from map01_overlap_controller_v23 import compile_cover

def main():
    extents=("pulse","short","medium","long")
    actions=("backward","strafe_left","strafe_right","fire","retreat_fire")
    atoms=[{"action":a,"extent":e} for a in actions for e in extents]
    policies=[()]
    tested=0
    for length in range(0,5):
        source=[()] if length==0 else itertools.product(atoms,repeat=length)
        for commands in source:
            steps=compile_cover(list(commands))
            assert len(steps)<=16 and sum(x["duration_ms"] for x in steps)==10000
            assert steps[-1]["op"]=="coast";tested+=1
    assert tested==168421
    print({"status":"passed","policies":tested})

if __name__=="__main__":main()
