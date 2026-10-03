"""Owned side-button custody with real XI2 decoding and inert transport.

This suite does not qualify a native server, ClientPointer association, changing
device topology, or concurrent physical input. Patches are scoped per method.
"""
import json
import struct
import types
import unittest
from unittest import mock

from Xlib import X
from Xlib.ext import xinput
from runtime.backends.x11_v1 import backend, session
from runtime.core_v1 import contract

class Clock:
    @staticmethod
    def monotonic_ns():
        return 1

    @staticmethod
    def sleep(value):
        raise RuntimeError('unplanned sleep')

def button_info(down,count=10):
    mask=sum(1<<n for n in down)
    raw=struct.pack('=HHHH',xinput.ButtonClass,3+count,2,count)+mask.to_bytes(4,'little')+struct.pack('='+str(count)+'I',*([0]*count))
    obj,tail=xinput.ButtonInfo.parse_binary(raw,None)
    if tail:raise RuntimeError('unconsumed synthetic class bytes')
    return obj
ORIGINAL_QUERY_DEVICE=xinput.XIQueryDevice
def wire_devices(down,count=10):
    mask=sum(1<<n for n in down)
    cls=struct.pack('=HHHH',xinput.ButtonClass,3+count,2,count)+mask.to_bytes(4,'little')+struct.pack('='+str(count)+'I',*([0]*count))
    name=b'pointer'
    dev=struct.pack('=HHHHHBB',2,xinput.MasterPointer,3,1,len(name),1,0)+name+b'\0'+cls
    raw=struct.pack('=BBHIH22x',1,0,5,len(dev)//4,1)+dev
    reply,tail=ORIGINAL_QUERY_DEVICE._reply.parse_binary(raw,None)
    if tail:raise RuntimeError('unconsumed synthetic reply bytes')
    return reply['devices']
class Endpoint:
    def __init__(self,stubborn=False):
        self.buttons=set();self.stubborn=stubborn;self.events=[];self.xi_fault=None;self.xi_extra=[];self.display=self
    def send(self,kind,number,**kw):
        self.events.append({'send':kind,'number':number})
        if kind==X.ButtonPress:self.buttons.add(number)
        elif kind==X.ButtonRelease and not self.stubborn:self.buttons.discard(number)
        else:
            if kind not in (X.ButtonPress,X.ButtonRelease):raise RuntimeError('unplanned event')
    def sync(self):self.events.append({'sync':True})
    def query_keymap(self):self.events.append({'keymap':True});return bytes(32)
    def query_pointer(self):
        self.events.append({'core_pointer':True})
        return types.SimpleNamespace(mask=sum(backend.BUTTON_MASKS.get(n,0) for n in self.buttons))
    def has_extension(self,name):self.events.append({'extension':name});return self.xi_fault!='missing_extension'
    def get_extension_major(self,name):
        if name!=xinput.extname:raise RuntimeError('wrong extension')
        return 131
    xinput_query_version=xinput.query_version
    xinput_query_device=xinput.query_device

def version_request(*,display,opcode,major_version,minor_version):
    if (opcode,major_version,minor_version)!=(131,2,0):raise RuntimeError('wrong actual wrapper version arguments')
    display.events.append({'xi_version':[major_version,minor_version]})
    return types.SimpleNamespace(major_version=2,minor_version=0)
def device_request(*,display,opcode,deviceid):
    if opcode!=131 or deviceid!=xinput.AllMasterDevices:raise RuntimeError('wrong actual wrapper device arguments')
    display.events.append({'xi_query':deviceid})
    if display.xi_fault=='throw':raise RuntimeError('inert XI query fault')
    if display.xi_fault=='empty':return types.SimpleNamespace(devices=[])
    cls=button_info(display.buttons,count=5 if display.xi_fault=='short' else 10)
    row=wire_devices(display.buttons,count=5 if display.xi_fault=='short' else 10)[0]
    if display.xi_fault=='missing_class':row.classes=[]
    if display.xi_fault=='disabled':row.enabled=False
    return types.SimpleNamespace(devices=[row]+display.xi_extra)
class SideButtonTests(unittest.TestCase):
    def setUp(self):
        for target, value in (
            ("runtime.backends.x11_v1.backend.time", Clock),
            ("Xlib.ext.xinput.XIQueryVersion", version_request),
            ("Xlib.ext.xinput.XIQueryDevice", device_request),
            ("runtime.backends.x11_v1.backend.xtest.fake_input",
             lambda d, kind, number, **kw: d.send(kind, number, **kw)),
        ):
            patcher = mock.patch(target, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def make(self,stubborn=False):
        b=backend.X11Backend.__new__(backend.X11Backend);d=Endpoint(stubborn);b.d=d;b.root=d;b.targets={};b.held_keycodes={};b.held_buttons=set();b.held_scroll_buttons=set();b.emissions=0;b._activation_supported=lambda:False
        return b,session.X11RuntimeSession(b)
    def dispatch(self,s,button):
        ops=[{'op':'pointer_button','button':button,'down':True},{'op':'pointer_button','button':button,'down':False},{'op':'release_all'}]
        p={'schema':contract.SCHEMA_PROGRAM,'program_id':'sidebutton-construction','source':{'observation_seq':7,'binding_revision':3},'authority':{'lease_id':'inert-owned-sidebutton','expires_at_ns':100},'terminal':{'release_all_required':True},'ops':ops}
        return s.dispatch(p,current_observation_seq=7,current_binding_revision=3,now_ns=1)
    def record(self,b,s,case,stage,call):
        try:r=call()
        except Exception as e:r={'exception':type(e).__name__,'detail':str(e)}
        print(json.dumps({'method':self.id(),'case':case,'stage':stage,'reply':r,'buttons':sorted(b.d.buttons),'owned':sorted(b.held_buttons),'quarantine':s.recovery_required,'emissions':b.emissions,'events':list(b.d.events)},sort_keys=True))
        return r
    def test_healthy_side_buttons(self):
        for button in ('x1','x2'):
            with self.subTest(button=button):
                b,s=self.make();r=self.record(b,s,button,'healthy',lambda:self.dispatch(s,button));self.assertEqual(r['status'],'completed');self.assertFalse(b.d.buttons or b.held_buttons or s.recovery_required)
    def test_stubborn_side_buttons(self):
        for button in ('x1','x2'):
            with self.subTest(button=button):
                b,s=self.make(True);r=self.record(b,s,button,'stubborn',lambda:self.dispatch(s,button));self.assertEqual(r['status'],'release_unverified');self.assertEqual(b.held_buttons,{button});self.assertTrue(s.recovery_required)
                before=b.emissions;r=self.record(b,s,button,'refused',lambda:self.dispatch(s,button));self.assertEqual(r['error'],'INPUT_RECOVERY_REQUIRED');self.assertEqual(b.emissions,before)
                r=self.record(b,s,button,'failed_recover',s.recover_input);self.assertEqual(r['status'],'recovery_failed');self.assertEqual(b.held_buttons,{button});self.assertTrue(s.recovery_required)
                b.d.stubborn=False;r=self.record(b,s,button,'recover',s.recover_input);self.assertEqual(r['status'],'input_recovered');self.assertFalse(b.d.buttons or b.held_buttons or s.recovery_required);self.assertIs(r['replay_allowed'],False);self.assertIsNone(r['task_success'])
                r=self.record(b,s,button,'fresh',lambda:self.dispatch(s,button));self.assertEqual(r['status'],'completed')
    def test_stubborn_left_control(self):
        b,s=self.make(True);r=self.record(b,s,'left','stubborn',lambda:self.dispatch(s,'left'));self.assertEqual(r['status'],'release_unverified');self.assertEqual(b.held_buttons,{'left'});self.assertTrue(s.recovery_required)
    def test_real_decoder_side_button_indices(self):
        for number in (8,9):
            state=button_info({number})['state'];self.assertTrue(state[number-1]);self.assertFalse(state[number]);self.assertEqual(len(state),10)
            print(json.dumps({'decoder_button':number,'state_length':len(state),'correct_index':number-1,'wrong_index':number,'correct_value':state[number-1],'wrong_value':state[number]},sort_keys=True))
    def test_unknown_xi_preserves_owned_custody(self):
        for fault in ('missing_extension','throw','empty','short','missing_class','disabled'):
            with self.subTest(fault=fault):
                b,s=self.make(True);b.d.xi_fault=fault;r=self.record(b,s,fault,'unknown',lambda:self.dispatch(s,'x2'));self.assertEqual(r['status'],'execution_failed');self.assertEqual(b.held_buttons,{'x2'});self.assertTrue(s.recovery_required)
                before=b.emissions;r=self.record(b,s,fault,'refused',lambda:self.dispatch(s,'x2'));self.assertEqual(r['error'],'INPUT_RECOVERY_REQUIRED');self.assertEqual(b.emissions,before)
                b.d.xi_fault=None;b.d.stubborn=False;r=self.record(b,s,fault,'recover',s.recover_input);self.assertEqual(r['status'],'input_recovered');self.assertFalse(b.d.buttons or b.held_buttons or s.recovery_required)

    def test_real_query_device_reply_shape(self):
        for number in (8,9):
            device=wire_devices({number})[0]
            self.assertEqual(device.deviceid,2);self.assertEqual(device.use,xinput.MasterPointer)
            self.assertIs(type(device.enabled),int);self.assertEqual(device.enabled,1);self.assertEqual(len(device.classes),1)
            self.assertIs(type(device.classes[0]['state']),xinput.ButtonMask)
            self.assertTrue(device.classes[0]['state'][number-1])
            print(json.dumps({'wire_button':number,'deviceid':device.deviceid,'use':device.use,'enabled':device.enabled,'classes':len(device.classes),'state_length':len(device.classes[0]['state'])},sort_keys=True))
    def test_second_master_stubborn_state_is_not_neutral(self):
        b,s=self.make();b.d.xi_extra=[types.SimpleNamespace(deviceid=4,use=xinput.MasterPointer,enabled=True,classes=[button_info({9})])]
        r=self.record(b,s,'second_master','down',lambda:self.dispatch(s,'x2'))
        self.assertEqual(r['status'],'release_unverified');self.assertEqual(b.held_buttons,{'x2'});self.assertTrue(s.recovery_required)
        b.d.xi_extra=[];r=self.record(b,s,'second_master','recover',s.recover_input);self.assertEqual(r['status'],'input_recovered')
    def test_duplicate_inventory_refuses_to_clear_custody(self):
        b,s=self.make(True);b.d.xi_extra=[types.SimpleNamespace(deviceid=2,use=xinput.MasterPointer,enabled=True,classes=[button_info(set())])]
        r=self.record(b,s,'duplicate_master','unknown',lambda:self.dispatch(s,'x1'));self.assertEqual(r['status'],'execution_failed');self.assertEqual(b.held_buttons,{'x1'});self.assertTrue(s.recovery_required)
        b.d.xi_extra=[];b.d.stubborn=False;r=self.record(b,s,'duplicate_master','recover',s.recover_input);self.assertEqual(r['status'],'input_recovered')

    def test_actual_query_version_wrapper_signature(self):
        d=Endpoint();r=d.xinput_query_version()
        self.assertEqual(r.major_version,2);self.assertEqual(r.minor_version,0)
        self.assertEqual(d.events,[{'xi_version':[2,0]}])
        print(json.dumps({'api_wrapper':'query_version','actual_positional_arguments':0,'major':r.major_version,'minor':r.minor_version},sort_keys=True))
