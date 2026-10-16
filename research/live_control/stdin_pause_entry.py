"""Test-only pause before the third command; owner/executor threads keep running."""
import sys,time
from pathlib import Path
import interactive_v23
marker=Path(sys.argv.pop(1));original=sys.stdin
class PausedInput:
    def __iter__(self):
        count=0
        while True:
            if count==2:
                marker.write_text(str(time.perf_counter_ns()));time.sleep(2)
            line=original.readline()
            if not line:break
            count+=1;yield line
sys.stdin=PausedInput()
interactive_v23.main()
