"""Fake-Xlib contract for batch release intervals on the current V12 owner."""
import sys, types, threading, time, unittest

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
from input_owner_v12 import InputOwner
from executor_v13 import Executor

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
            self.assertIn("key_release_intervals_ns",record)
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
            executor=object.__new__(Executor)
            event=executor._release_event("intent-v12",{"intent_token":lease.intent_token,"record":record})
            self.assertEqual(event["event"],"input_released")
            self.assertEqual(event["owner_release"]["key_release_intervals_ns"],intervals)
        finally: owner.close()

    def test_explicit_up_retains_post_sync_cancel_receipt(self):
        owner=InputOwner(":fake"); lease=Lease()
        try:
            owner.call("down",lease,"W")
            SERVER["release_hook"]=lease.cancel.set
            owner.call("up",lease,"W")
            receipt=next(row for row in owner.records if row.get("event")=="owner_explicit_keyup")
            self.assertTrue(receipt["cancel_requested_after_sync"])
            self.assertTrue(receipt["server_sync_completed"])
        finally: owner.close()

if __name__=="__main__": unittest.main(verbosity=2)
