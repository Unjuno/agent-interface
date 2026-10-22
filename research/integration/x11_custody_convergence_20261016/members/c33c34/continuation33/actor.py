import sys, pathlib, struct, json, unittest
ROOT = pathlib.Path(__file__).resolve().parent
BASE = ROOT.parent / 'x11-package-import-01a0ff2c' / 'dependencies'
sys.path[:0] = [str(BASE/'python_xlib-0.33-py2.py3-none-any.whl'), str(BASE/'six-1.17.0-py2.py3-none-any.whl')]
from Xlib.protocol import rq

def audit(event, args):
    if event.startswith(('socket.', 'ctypes.dlopen', 'subprocess.', 'os.system', 'os.spawn', 'os.exec')):
        raise RuntimeError('native/process operation forbidden: '+event)
sys.addaudithook(audit)

class DeviceButton(rq.Request):
    # Private protocol construction, not an installed Python-Xlib extension.
    _request = rq.Struct(rq.Card8('opcode'), rq.Opcode(2), rq.RequestLength(),
        rq.Card8('event_type'), rq.Card8('detail'), rq.Pad(2),
        rq.Card32('time'), rq.Card32('root'), rq.Pad(8),
        rq.Int16('x'), rq.Int16('y'), rq.Pad(7), rq.Card8('deviceid'))

class Endpoint:
    def __init__(self): self.requests=[]
    def send_request(self, request, onerror): self.requests.append(request._binary)

def encode(device, press=True):
    if type(device) is not int or not 2 <= device <= 127:
        raise ValueError('XI1 seven-bit device ID required')
    ep=Endpoint()
    DeviceButton(display=ep, opcode=132, event_type=64+(3 if press else 4),
                 detail=9,time=0,root=0,x=0,y=0,deviceid=device)
    return ep.requests[0]

def route(packet, current):
    # Inert oracle from pinned xtest.c; synthetic-source state only.
    event=packet[4]&127
    return packet[35]&127 if event>=64 else current

def row(name, **kw): print(json.dumps(dict(case=name,**kw),sort_keys=True))

class Tests(unittest.TestCase):
    def test_exact_wire_down_and_up(self):
        for press in (True,False):
            p=encode(7,press)
            expected=struct.pack('=BBHBBHII8xhh7xB',132,2,9,67 if press else 68,9,0,0,0,0,0,7)
            self.assertEqual(p,expected);self.assertEqual(len(p),36)
            row('wire',press=press,hex=p.hex(),target=7)
    def test_core_device_field_does_not_select_target(self):
        p=bytearray(encode(7));p[4]=4
        self.assertEqual(route(p,4),4)
        row('core_negative',declared_device=7,current=4,target=route(p,4))
    def test_switch_between_observation_and_send(self):
        p=encode(7)
        self.assertEqual(route(p,4),7)
        row('switch',before=2,current=4,target=route(p,4))
    def test_ABA_before_after_observations(self):
        p=encode(7)
        self.assertEqual(route(p,4),7)
        row('ABA',before=2,send_current=4,after=2,target=route(p,4))
    def test_invalid_ids_rejected_before_encoding(self):
        for d in (0,1,128,135,256,-1,True,None,'7'):
            with self.assertRaises(ValueError): encode(d)
        p=bytearray(encode(7));p[35]=135
        self.assertEqual(route(p,4),7)
        row('alias_negative',wire_id=135,server_target=7,rejected_inputs=9)
    def test_ID_reuse_is_not_generation_fencing(self):
        down=encode(7);up=encode(7,False)
        generations={7:'original'}
        down_generation=generations[route(down,2)]
        generations[7]='replacement'
        up_generation=generations[route(up,4)]
        self.assertNotEqual(down_generation,up_generation)
        row('reuse_residual',down_generation=down_generation,up_generation=up_generation,adoption='HOLD')

if __name__=='__main__': unittest.main(verbosity=2)
