"""Fake-Xlib regression for per-key batch cleanup release bounds.

The bound is request-start through successful batch XSync completion; it does
not claim a hardware transition or application-consumption timestamp.
"""
import sys, types, threading, time, unittest
from unittest.mock import patch

SERVER = {"down": set(), "lock": threading.Lock(), "release_hook": None}

class FakeRoot:
    def query_pointer(self): return types.SimpleNamespace(mask=0)

class FakeDisplay:
    def __init__(self, _name=None): self.root=FakeRoot(); self.events=[]
    def get_input_focus(self): return types.SimpleNamespace(focus=42)
    def keysym_to_keycode(self, sym): return sym % 200 + 10
    def query_keymap(self):
        out=bytearray(32)
        with SERVER["lock"]:
            for code in SERVER["down"]: out[code//8] |= 1 << (code%8)
        return bytes(out)
    def screen(self): return types.SimpleNamespace(root=self.root)
    def sync(self):
        if self.events and self.events[-1][0] == 3 and SERVER["release_hook"]:
            hook, SERVER["release_hook"] = SERVER["release_hook"], None
            hook()
    def close(self): pass

def fake_input(d, event, code, **_kwargs):
    d.events.append((event,code))
    with SERVER["lock"]:
        if event == 2: SERVER["down"].add(code)
        elif event == 3: SERVER["down"].discard(code)
        else: raise AssertionError(event)

xlib=types.ModuleType("Xlib"); xlib.__path__=[]
xlib.X=types.SimpleNamespace(KeyPress=2,KeyRelease=3,ButtonRelease=5,ButtonPress=4,
                              Button1Mask=1,AnyPropertyType=0,IsViewable=2,MotionNotify=6)
xlib.XK=types.SimpleNamespace(string_to_keysym=lambda value: ord(value[0]))
xlib.display=types.SimpleNamespace(Display=FakeDisplay)
xlib.error=types.SimpleNamespace(BadWindow=type("BadWindow",(Exception,),{}),BadDrawable=type("BadDrawable",(Exception,),{}))
ext=types.ModuleType("Xlib.ext"); ext.__path__=[]
xtest=types.ModuleType("Xlib.ext.xtest"); xtest.fake_input=fake_input; ext.xtest=xtest; xlib.ext=ext
sys.modules.update({"Xlib":xlib,"Xlib.ext":ext,"Xlib.ext.xtest":xtest})
from input_owner_v10 import InputOwner as Base
from input_owner_v11 import InputOwner as Telemetry
from input_owner_v13 import InputOwner

class Lease:
    def __init__(self):
        self.deadline=time.perf_counter_ns()+5_000_000_000
        self.intent_token="test-intent"
        self.cancel=threading.Event()
        self.expected_focus=42
    def check(self):
        if time.perf_counter_ns() >= self.deadline: raise TimeoutError("expired")
        if self.cancel.is_set(): raise RuntimeError("cancelled")

class BatchReleaseTelemetryTests(unittest.TestCase):
    def tearDown(self):
        with SERVER["lock"]: SERVER["down"].clear()
        SERVER["release_hook"]=None

    def test_cancelled_batch_release_records_a_bound_for_each_key(self):
        owner=InputOwner(":fake"); lease=Lease()
        try:
            owner.call("down",lease,"W")
            owner.call("down",lease,"A")
            lease.cancel.set()
            deadline=time.monotonic()+1
            while not owner.records and time.monotonic()<deadline:
                time.sleep(.001)
            self.assertEqual(len(owner.records),1)
            record=owner.records[0]
            self.assertEqual(record["reason"],"cancelled")
            intervals=record["key_release_intervals_ns"]
            expected=[ord("W")%200+10,ord("A")%200+10]
            self.assertEqual([item["keycode"] for item in intervals],expected)
            self.assertEqual(len(intervals),2)
            for item in intervals:
                start,end=item["interval_ns"]
                self.assertIs(type(start),int)
                self.assertIs(type(end),int)
                self.assertLessEqual(start,end)
                self.assertLessEqual(end,record["verified_ns"])
            self.assertTrue(record["verified"])

    def test_explicit_up_keeps_existing_v11_release_interval_receipt(self):
        owner=InputOwner(":fake"); lease=Lease()
        try:
            owner.call("down",lease,"W")
            receipt=owner.call("up",lease,"W")
            self.assertEqual(receipt["event"],"input_release_rpc")
            self.assertEqual(receipt["operation"],"up")
            self.assertTrue(owner.records == [])
        finally: owner.close()

    def test_v13_keeps_v11_wrapper(self):
        self.assertTrue(issubclass(InputOwner, Telemetry))
        owner=object.__new__(InputOwner); owner.owner_id="owner-v13"; lease=Lease()
        with patch.object(Base,"call",return_value=None), patch("input_owner_v11.time.perf_counter_ns",side_effect=[100,145]):
            receipt=owner.call("up",lease,"space")
        self.assertEqual(receipt["release_transition_interval_ns"],[100,145])

if __name__=="__main__": unittest.main(verbosity=2)
