import json,tempfile
from pathlib import Path
from experiment import build_case,writej
from binding_guard import binding_failures

def run():
    with tempfile.TemporaryDirectory() as d:
        r=Path(d)/'x';build_case(r,570_000_000);assert binding_failures(r)==[]
        p=json.loads((r/'summary.json').read_text());p['pairs'][0]['recovery_no_retained_input_upper_ns']=480_000_000;writej(r/'summary.json',p)
        got=binding_failures(r);assert got==['pair1:bounded_recovery:recovery_no_retained_input_upper_ns:summary_arm_mismatch'],got
    print('PASS binding_guard 2/2')
if __name__=='__main__':run()
