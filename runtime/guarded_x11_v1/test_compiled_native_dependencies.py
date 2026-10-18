"""Fresh compiled dependencies through the actual bridge, Fake X transport only."""
import copy
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from PIL import Image
from Xlib import X
from runtime.cli_v1.test_mcp_process_identity import FakeX
from runtime.guarded_x11_v1.bridge import NativeHandleBridge
from runtime.guarded_x11_v1.compiled import _Adapter
from research.live_control.integrated_efficiency_compiled_adapter_v2 import (
    compile_form_method, EXPECTED_METHOD_CONTRACT,
)

ROWS = []


class CompiledNativeDependencyTests(unittest.TestCase):
    def test_missing_guard_capability_is_rejected_before_capture(self):
        from runtime.guarded_x11_v1 import test_compiled as fixture
        bridge=fixture.Bridge();bridge.input_guard=None
        with self.assertRaisesRegex(ValueError,'input guard'):
            _Adapter(bridge,fixture.spec(),fixture.bindings(),fixture.perceive,fixture.verify,lambda:False)
        self.assertEqual(bridge.sequence,0);self.assertEqual(bridge.inputs,[])

    def cell(self, interaction='keyboard', change='false'):
        fake=FakeX(self);pointer=[0,0];buttons=set();events=[];reads=[]
        def marker(value):
            image=Image.frombytes('RGB',(32,32),fake.raw,'raw','BGRX')
            image.putpixel((31,31),(value,0,0));fake.raw=image.tobytes('raw','BGRX')
        marker(1)
        fake.backend.root.query_pointer=lambda:SimpleNamespace(root_x=pointer[0],root_y=pointer[1],
            mask=X.Button1Mask if buttons else 0)
        original_emit=fake.emit
        def emit(display,kind,code=0,**kwargs):
            events.append([kind,code,copy.deepcopy(kwargs)])
            if kind==X.MotionNotify:
                pointer[:]=[kwargs['x'],kwargs['y']]
                if change=='after_motion':marker(0)
            elif kind==X.ButtonPress:buttons.add(code)
            elif kind==X.ButtonRelease:buttons.discard(code)
            else:
                original_emit(display,kind,code)
                if kind==X.KeyPress and code==1 and change=='held':marker(0)
        with tempfile.TemporaryDirectory(prefix='compiled-dependency-') as td,patch(
                'runtime.backends.x11_v1.backend.xtest.fake_input',side_effect=emit):
            bridge=NativeHandleBridge(None,{'app':20},'app',Path(td)/'bridge',process_identity=True)
            try:
                source=bridge.observe()
                offsets={a:bridge.mint(a,source['sequence'],p,region_size=[12,12])
                    for a,p in [('field',[8,8]),('submit',[24,8])]}
                interface=compile_form_method(interface_id='dependency-test',session_scope=bridge.scope,
                    surface='x11-window-20',field_handle='field',submit_handle='submit',
                    method_contract=EXPECTED_METHOD_CONTRACT)
                def perceive(native,image):
                    n=image.getpixel((31,31))[0]
                    reads.append(dict(sequence=native['sequence'],marker=n))
                    if n==4:raise OSError('owned perception unavailable')
                    return dict(field_target_present=n!=5,submit_target_present=n!=5,
                        field_pixels_changed=True,field_value_matches_task='unknown' if n==3 else n==1,
                        submission_pixels_changed=False)
                bindings={a:dict(interaction=interaction,offset=offsets[alias],tail=
                    [{'op':'key_chord','keys':['CTRL','a']}] if interaction=='keyboard' else [])
                    for a,alias in [('enter_token','field'),('submit_form','submit')]}
                adapter=_Adapter(bridge,interface,bindings,perceive,
                    lambda *a:{'status':'unavailable','evidence_ref':'synthetic'},lambda:False)
                observation=adapter.observe({})
                admission=adapter.admit(dict(interface_id=interface['interface_id'],session_scope=bridge.scope,
                    action='submit_form',operation='activate_submit',symbol=interface['symbols']['submit_control'],
                    observation=observation))
                self.assertTrue(admission['eligible'])
                if change in ('false','unknown','exception','missing'):
                    marker({'false':0,'unknown':3,'exception':4,'missing':5}[change])
                if change=='expired':admission['valid_until_ns']=time.monotonic_ns()-1
                result=adapter.execute(dict(action='submit_form',operation='activate_submit',
                    authorization=admission['authorization'],expected_sequence=observation['sequence'],
                    valid_until_ns=admission['valid_until_ns']))
                row=dict(interaction=interaction,change=change,result=result,events=events,
                    down=sorted(fake.down),buttons=sorted(buttons),reads=reads,
                    guard_restored=bridge._input_guard is None,pending_authorizations=len(adapter.authorizations),
                    files_hex={p.relative_to(td).as_posix():p.read_bytes().hex()
                        for p in Path(td).rglob('*') if p.is_file()})
                ROWS.append(row)
                self.assertEqual(row['down'],[]);self.assertEqual(row['buttons'],[])
                self.assertTrue(row['guard_restored']);self.assertEqual(row['pending_authorizations'],0)
                return row
            finally:bridge.close()

    def test_stable_dependencies_allow_each_interaction(self):
        for interaction in ('keyboard','click','move'):
            with self.subTest(interaction=interaction):
                row=self.cell(interaction,'stable')
                self.assertEqual(row['result']['status'],'completed')
                self.assertTrue(row['result']['release']['verified'])
                self.assertGreater(len(row['reads']),1)
                self.assertEqual(len(row['events']),{'keyboard':4,'click':3,'move':1}[interaction])

    def test_false_dependency_stops_each_interaction_before_input(self):
        for interaction in ('keyboard','click','move'):
            with self.subTest(interaction=interaction):
                row=self.cell(interaction,'false')
                self.assertEqual(row['events'],[])
                self.assertIs(row['result']['input_dispatched'],False)

    def test_unknown_dependency_stops_each_interaction_before_input(self):
        for interaction in ('keyboard','click','move'):
            with self.subTest(interaction=interaction):self.assertEqual(self.cell(interaction,'unknown')['events'],[])

    def test_lost_identity_stops_each_interaction(self):
        for interaction in ('keyboard','click','move'):
            with self.subTest(interaction=interaction):self.assertEqual(self.cell(interaction,'missing')['events'],[])

    def test_perception_exception_stops_each_interaction(self):
        for interaction in ('keyboard','click','move'):
            with self.subTest(interaction=interaction):self.assertEqual(self.cell(interaction,'exception')['events'],[])

    def test_change_while_modifier_held_stops_suffix_and_releases(self):
        row=self.cell('keyboard','held')
        self.assertEqual([e[:2] for e in row['events']],[[X.KeyPress,1],[X.KeyRelease,1]])
        self.assertTrue(row['result']['release']['verified'])
        self.assertNotEqual(row['result']['status'],'completed')

    def test_hover_change_stops_button_press_and_releases(self):
        row=self.cell('click','after_motion')
        self.assertEqual([e[0] for e in row['events']],[X.MotionNotify])
        self.assertTrue(row['result']['release']['verified'])
        self.assertNotEqual(row['result']['status'],'completed')

    def test_expired_authorization_never_rechecks_or_dispatches(self):
        row=self.cell('keyboard','expired')
        self.assertEqual(row['events'],[]);self.assertEqual(len(row['reads']),1)
        self.assertIs(row['result']['input_dispatched'],False)


if __name__=='__main__':unittest.main()
