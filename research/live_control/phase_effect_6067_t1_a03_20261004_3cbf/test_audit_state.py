import unittest
from pathlib import Path
import reference as ref
from audit_runner import admit_audit_state
ROOT=Path(__file__).resolve().parent.parent/'source_deadline_probe_6067_b01_20261003_3cbf'

def example():
    f=ref.read(ROOT/'FREEZE.json')
    state=ref.parse_record(ref.read(ROOT/'native-raw/launch.json')['inspect_stdout'])
    f['audit_native_argv']=['python3','-B','/src/saved_audit.py']
    state['Config']['Cmd']=f['audit_native_argv']
    state['Mounts'].append({'Type':'bind','Source':f['guest_wrapper'],'Destination':'/raw','RW':False})
    next(m for m in state['Mounts'] if m['Destination']=='/out')['Source']=f['guest_audit']
    state['State']['ExitCode']=0
    return state,f

class AuditState(unittest.TestCase):
    def test_exact_terminal_zero_and_three_mounts(self):
        state,f=example();admit_audit_state(state,f,0)
    def test_boolean_or_float_exit_never_terminal_zero(self):
        for value in (False,0.0):
            state,f=example();state['State']['ExitCode']=value
            with self.assertRaises(ValueError):admit_audit_state(state,f,0)
            state,f=example()
            with self.assertRaises(ValueError):admit_audit_state(state,f,value)

if __name__=='__main__':unittest.main()
