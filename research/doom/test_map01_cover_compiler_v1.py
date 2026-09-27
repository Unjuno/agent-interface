"""Exhaust every schema-v2 cover command combination through the v22 compiler."""
import itertools
from map01_overlap_controller_v22 import compile_cover

def main():
    extents=("pulse","short","medium","long")
    actions=("backward","strafe_left","strafe_right","fire","retreat_fire")
    tested=0
    for extent in extents:
        steps=compile_cover([{"action":"coast","extent":extent}])
        assert len(steps)<=16 and sum(x["duration_ms"] for x in steps)==10000
        assert steps[-1]["op"]=="coast";tested+=1
    atoms=[{"action":a,"extent":e} for a in actions for e in extents]
    for length in range(1,5):
        for commands in itertools.product(atoms,repeat=length):
            steps=compile_cover(list(commands))
            assert len(steps)<=16 and sum(x["duration_ms"] for x in steps)==10000
            assert steps[-1]["op"]=="coast";tested+=1
    assert tested==168424
    print({"status":"passed","policies":tested})

if __name__=="__main__":main()
