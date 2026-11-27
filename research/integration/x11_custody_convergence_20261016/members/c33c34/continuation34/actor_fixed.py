"""Actual V4 access-suppression counterexample; no native actor."""
import sys,pathlib,json,types,struct,unittest
from unittest import mock
P=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(P/'source'))
for n in ('python_xlib-0.33-py2.py3-none-any.whl','six-1.17.0-py2.py3-none-any.whl'):
    sys.path.insert(0,str(P.parent/'x11-package-import-01a0ff2c'/'dependencies'/n))
FORBIDDEN=[]
def audit(event,args):
    if event.startswith(('socket.','ctypes.dlopen','subprocess.','os.system','os.spawn','os.exec')):
        FORBIDDEN.append(event);raise RuntimeError('forbidden '+event)
sys.addaudithook(audit)
from Xlib import X,display
from Xlib.ext import xinput
display.Display=lambda *a,**kw: (_ for _ in ()).throw(RuntimeError('native Display forbidden'))
from runtime.backends.x11_v1 import backend,session,test_sidebutton_ledger as fixture
from runtime.core_v1 import contract
for mod in (backend,session,fixture,contract):
    if not pathlib.Path(mod.__file__).resolve().is_relative_to((P/'source').resolve()):raise RuntimeError('source origin')
QUERY_REPLY=xinput.XIQueryDevice._reply
PROPERTY_REPLY=xinput.XIGetProperty._reply

def device_wire(down,deviceid=2,use=xinput.MasterPointer,attachment=3,name=b'pointer',sourceid=7):
    count=10
    # Server ListButtonInfo copies native down bits; real ButtonMask indexes n-1.
    mask=sum(1<<n for n in down)
    cls=struct.pack('=HHHH',xinput.ButtonClass,3+count,sourceid,count)+mask.to_bytes(4,'little')+bytes(count*4)
    dev=struct.pack('=HHHHHBB',deviceid,use,attachment,1,len(name),1,0)+name+bytes((-len(name))%4)+cls
    return struct.pack('=BBHIH22x',1,0,5,len(dev)//4,1)+dev

class Endpoint(fixture.Endpoint):
    def __init__(self,denied=False,stubborn=False):
        super().__init__(stubborn);self.denied=denied;self.query_packets=[];self.property_packets=[]
    xinput_get_device_property=xinput.get_device_property

def device_request(*,display,opcode,deviceid):
    if (opcode,deviceid)!=(131,xinput.AllMasterDevices):raise RuntimeError('wrong real query wrapper arguments')
    display.events.append({'xi_query':deviceid})
    # Explicit source-supported XACE profile: GetAttr succeeds, Read denied.
    raw=device_wire(set() if display.denied else display.buttons)
    display.query_packets.append(raw)
    reply,tail=QUERY_REPLY.parse_binary(raw,None)
    if tail:raise RuntimeError('reply tail')
    return types.SimpleNamespace(devices=reply['devices'])

def property_request(*,display,opcode,deviceid,property,type,offset,length,delete):
    if (opcode,deviceid,property,type,offset,length,delete)!=(131,7,42,19,0,1,False):raise RuntimeError('actual property wrapper arguments')
    raw=struct.pack('=BBHIIIIB11x',1,0,6,1,19,0,1,8)+b'\1\0\0\0'
    display.property_packets.append(raw)
    reply,tail=PROPERTY_REPLY.parse_binary(raw,None,rawdict=True)
    if tail:raise RuntimeError('property reply tail')
    return types.SimpleNamespace(**reply)

class Tests(unittest.TestCase):
    def setUp(self):
        for target,value in (
            ('runtime.backends.x11_v1.backend.time',fixture.Clock),
            ('Xlib.ext.xinput.XIQueryVersion',fixture.version_request),
            ('Xlib.ext.xinput.XIQueryDevice',device_request),
            ('Xlib.ext.xinput.XIGetProperty',property_request),
            ('runtime.backends.x11_v1.backend.xtest.fake_input',lambda d,k,n,**kw:d.send(k,n,**kw))):
            p=mock.patch(target,value);p.start();self.addCleanup(p.stop)
    def make(self,denied=False,stubborn=False):
        b=backend.X11Backend.__new__(backend.X11Backend);d=Endpoint(denied,stubborn)
        b.d=d;b.root=d;b.targets={};b.held_keycodes={};b.held_buttons=set();b.held_scroll_buttons=set();b.emissions=0;b._activation_supported=lambda:False
        return b,session.X11RuntimeSession(b)
    def dispatch(self,s):
        ops=[{'op':'pointer_button','button':'x2','down':True},{'op':'pointer_button','button':'x2','down':False},{'op':'release_all'}]
        p={'schema':contract.SCHEMA_PROGRAM,'program_id':'state-access-construction','source':{'observation_seq':7,'binding_revision':3},'authority':{'lease_id':'inert-owned-sidebutton','expires_at_ns':100},'terminal':{'release_all_required':True},'ops':ops}
        return s.dispatch(p,current_observation_seq=7,current_binding_revision=3,now_ns=1)
    def record(self,b,s,case,r):
        print(json.dumps({'case':case,'reply':r,'synthetic_source_buttons':sorted(b.d.buttons),'owned':sorted(b.held_buttons),'quarantine':s.recovery_required,'emissions':b.emissions,'query_packets':[p.hex() for p in b.d.query_packets],'events':b.d.events},sort_keys=True))
    def test_visible_stubborn_control(self):
        b,s=self.make(stubborn=True);r=self.dispatch(s);self.record(b,s,'visible_stubborn',r)
        self.assertEqual(r['status'],'release_unverified');self.assertEqual(b.held_buttons,{'x2'});self.assertTrue(s.recovery_required);self.assertEqual(b.d.buttons,{9})
    def test_suppressed_stubborn_must_not_clear_custody(self):
        b,s=self.make(denied=True,stubborn=True);r=self.dispatch(s);self.record(b,s,'suppressed_stubborn',r)
        self.assertEqual(b.d.buttons,{9})
        self.assertNotEqual(r['status'],'completed','valid zero inventory suppressed by source-supported read denial is not neutral proof')
        self.assertEqual(b.held_buttons,{'x2'});self.assertTrue(s.recovery_required)
    def test_XI1_suppressed_state_is_indistinguishable(self):
        # Exact xQueryDeviceStateReply + xButtonState layout from pinned XIproto.
        def wire(actual_down,denied):
            mask=sum(1<<n for n in (() if denied else actual_down))
            cls=struct.pack('=BBBB',1,36,10,0)+mask.to_bytes(32,'little')
            return struct.pack('=BBHIB23x',1,30,7,9,1)+cls
        neutral=wire(set(),False);suppressed=wire({9},True);visible=wire({9},False)
        self.assertEqual(neutral,suppressed);self.assertNotEqual(neutral,visible)
        self.assertEqual(len(neutral),68)
        print(json.dumps({'case':'XI1_indistinguishable','neutral_hex':neutral.hex(),'suppressed_hex':suppressed.hex(),'visible_hex':visible.hex(),'state_readable_flag':False},sort_keys=True))
    def test_fixed_XTEST_marker_is_not_generation_identity(self):
        records=[]
        for generation in ('original','replacement'):
            d=Endpoint();prop=d.xinput_get_device_property(7,42,19,0,1)
            raw=device_wire(set(),7,xinput.SlavePointer,2,b'Virtual core XTEST pointer',7)
            device,tail=QUERY_REPLY.parse_binary(raw,None);self.assertFalse(tail)
            info=device['devices'][0]
            self.assertEqual((info.deviceid,info.use,info.attachment,info.enabled),(7,xinput.SlavePointer,2,1))
            self.assertEqual(prop.type,19);self.assertEqual(prop.bytes_after,0)
            self.assertEqual(prop.value,(8,b'\1'))
            records.append({'generation_scorer_only':generation,'inventory_hex':raw.hex(),'marker_hex':d.property_packets[0].hex(),'property_value':[prop.value[0],list(prop.value[1])]})
        self.assertEqual(records[0]['inventory_hex'],records[1]['inventory_hex']);self.assertEqual(records[0]['marker_hex'],records[1]['marker_hex'])
        print(json.dumps({'case':'generation_marker_indistinguishable','observations':records,'adoption':'HOLD'},sort_keys=True))

if __name__=='__main__':
    suite=unittest.TestSuite([Tests('test_fixed_XTEST_marker_is_not_generation_identity')])
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({'summary':True,'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'forbidden':FORBIDDEN},sort_keys=True))
    sys.exit(not result.wasSuccessful())
