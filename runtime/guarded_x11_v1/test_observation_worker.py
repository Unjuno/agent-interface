"""Actual guarded bridge, separate Fake X capture client, public cleanup."""
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from Xlib import X
from runtime.backends.x11_v1.backend import X11Backend
from runtime.cli_v1.test_mcp_process_identity import FakeX
from .bridge import NativeHandleBridge


def reader_backend(fake, get_image):
    backend = object.__new__(X11Backend)
    visual = SimpleNamespace(visual_id=1,red_mask=0xff0000,green_mask=0xff00,blue_mask=0xff,visual_class=X.TrueColor)
    info = SimpleNamespace(image_byte_order=0,pixmap_formats=[SimpleNamespace(depth=24,bits_per_pixel=32,scanline_pad=32)],
        roots=[SimpleNamespace(allowed_depths=[SimpleNamespace(visuals=[visual])])])
    window = SimpleNamespace(id=20)
    backend.targets = {'app':window}
    backend.d = SimpleNamespace(get_input_focus=lambda:SimpleNamespace(focus=window),
        screen=lambda:SimpleNamespace(width_in_pixels=32,height_in_pixels=32),
        display=SimpleNamespace(info=info),close=lambda:None)
    backend.root = SimpleNamespace(get_image=get_image)
    backend.geometry = lambda target:dict(x=0,y=0,width=32,height=32)
    backend.capture_artifacts = None
    return backend


class ObservationWorkerTests(unittest.TestCase):
    def exercise(self,boundary,trigger):
        from .observation_worker import X11ObservationReader
        fake = FakeX(self)
        focus = [20]
        fake.backend.d.get_input_focus = lambda:SimpleNamespace(focus=SimpleNamespace(id=focus[0]))
        fake.backend.d.create_resource_object = lambda kind,xid:SimpleNamespace(id=xid)
        fake.backend.d.get_display_name = lambda:':fake-qualified'
        entered,resume,closed = [threading.Event() for _ in range(3)]
        now = [1_000_000]
        results,errors,reader_threads = [],[],[]
        def gate():
            entered.set()
            if not resume.wait(5): raise TimeoutError('test did not resume dependency')
        def image(*args):
            reader_threads.append(threading.get_ident())
            if boundary=='capture' and 1 in fake.down: gate()
            return SimpleNamespace(data=fake.raw,depth=24,visual=1)
        backend = reader_backend(fake,image)
        backend.d.get_input_focus = lambda:SimpleNamespace(focus=SimpleNamespace(id=focus[0]))
        backend.d.create_resource_object = lambda kind,xid:SimpleNamespace(id=xid)
        backend.d.close = lambda:closed.set()
        saved = X11ObservationReader._save
        def save(reader,name,value):
            reader_threads.append(threading.get_ident())
            if boundary=='persistence' and name.startswith('observation-') and 1 in fake.down: gate()
            return saved(reader,name,value)
        def verify(stage,source,image):
            reader_threads.append(threading.get_ident())
            if boundary=='callback' and 1 in fake.down: gate()
            return True
        with tempfile.TemporaryDirectory() as td, \
                patch('time.monotonic_ns',side_effect=lambda:now[0]), \
                patch('runtime.guarded_x11_v1.observation_worker.open_readonly_backend',return_value=backend), \
                patch('runtime.guarded_x11_v1.observation_worker.read_linux_x11_process_identity',side_effect=lambda *args:fake.generation), \
                patch.object(X11ObservationReader,'_save',save), \
                patch('runtime.guarded_x11_v1.target_queries.X11TargetQueries') as query:
            query.return_value.read.side_effect = lambda op,xid:True if op=='focus' else fake.generation
            bridge = NativeHandleBridge(':fake-qualified',{'app':20},'app',td+'/bridge',
                        process_identity=True,query_worker=True,observation_worker=True)
            source = bridge.observe()
            offset = bridge.mint('field',source['sequence'],[8,8],region_size=[12,12])
            tail = [{'op':'key_chord','keys':['CTRL','a']}]
            def invoke():
                try:
                    with bridge.cancellation_scope('only-call'),bridge.input_guard('field',offset,tail=tail,verify=verify):
                        results.append(bridge.keyboard('field',offset,tail=tail))
                except BaseException as error: errors.append(error)
            worker = threading.Thread(target=invoke)
            worker.start()
            try:
                if boundary not in ('healthy','retarget'):
                    self.assertTrue(entered.wait(2),(results,errors))
                    sequence = bridge.sequence
                    self.assertEqual(fake.down,{1})
                    if trigger=='cancel': self.assertEqual(bridge.request_cancel('only-call')['status'],'cancel_requested')
                    elif trigger=='expiry': now[0]=bridge.deadline
                    elif trigger=='context': bridge.binding_revision+=1;resume.set()
                    elif trigger=='generation': fake.generation='b'*64;resume.set()
                    worker.join(2)
                    self.assertFalse(worker.is_alive(),(results,errors))
                    self.assertEqual(errors,[])
                    self.assertEqual(results[0]['status'],'execution_failed')
                    self.assertTrue(results[0]['execution']['releases'][-1]['verified'])
                    self.assertEqual(fake.down,set())
                    self.assertEqual(fake.emissions,[(X.KeyPress,1),(X.KeyRelease,1)])
                    if trigger in ('cancel','expiry'): self.assertFalse(resume.is_set())
                    self.assertTrue(bridge.review_required)
                    self.assertTrue(bridge._observations.snapshot()['retired'])
                    resume.set();self.assertTrue(closed.wait(2))
                    self.assertEqual(bridge.sequence,sequence)
                else:
                    worker.join(2)
                    self.assertFalse(worker.is_alive());self.assertEqual(errors,[])
                    self.assertEqual(results[0]['status'],'completed')
                    self.assertEqual(fake.emissions,[(2,1),(2,2),(3,2),(3,1)])
                    self.assertEqual(fake.down,set())
                    if boundary=='retarget':
                        focus[0] = 21
                        reviewed = bridge.review_window(21)
                        self.assertEqual(reviewed['status'],'reviewed',reviewed)
                        offset = bridge.mint('reviewed',reviewed['observation']['sequence'],[8,8],region_size=[12,12])
                        with bridge.cancellation_scope('new-call'):
                            second = bridge.keyboard('reviewed',offset,tail=tail)
                        self.assertEqual(second['status'],'completed',second)
                        self.assertEqual(backend.targets['app'].id,21)
                self.assertNotIn(worker.ident,reader_threads)
            finally:
                resume.set();worker.join(5);bridge.close()

    def test_healthy(self): self.exercise('healthy','none')
    def test_reviewed_new_window_uses_current_target_on_reader_client(self): self.exercise('retarget','none')
    def test_capture_cancel(self): self.exercise('capture','cancel')
    def test_capture_expiry(self): self.exercise('capture','expiry')
    def test_persistence_cancel(self): self.exercise('persistence','cancel')
    def test_persistence_expiry(self): self.exercise('persistence','expiry')
    def test_callback_cancel(self): self.exercise('callback','cancel')
    def test_callback_expiry(self): self.exercise('callback','expiry')
    def test_changed_context_refuses_capture_reply(self): self.exercise('capture','context')
    def test_changed_generation_refuses_capture_reply(self): self.exercise('capture','generation')

    def test_compiled_call_cancel_scope_accepts_idle_cancel_but_input_scope_does_not(self):
        bridge=object.__new__(NativeHandleBridge)
        bridge._target_queries=object();bridge._cancel_lock=threading.Lock()
        bridge._used_cancel_tokens=set();bridge._cancel_ticket=None
        bridge.active=None;bridge.review_required=False
        with bridge.cancellation_scope('compiled',cancel_when_idle=True):
            result=bridge.request_cancel('compiled')
            self.assertEqual(result['status'],'cancel_requested')
            self.assertTrue(bridge._cancel_requested())
            self.assertTrue(bridge.review_required)
        bridge.review_required=False
        with bridge.cancellation_scope('input'):
            result=bridge.request_cancel('input')
            self.assertEqual(result['status'],'not_active')


class ReadOnlyClientTests(unittest.TestCase):
    def test_open_uses_only_separate_read_client_without_xtest_requirement(self):
        from .observation_worker import open_readonly_backend
        calls = []
        window,root = SimpleNamespace(id=20),object()
        class Connection:
            def screen(self): return SimpleNamespace(root=root)
            def create_resource_object(self,kind,xid):
                calls.append((kind,xid));return window
            def close(self): calls.append('closed')
        connection = Connection()
        with patch('runtime.guarded_x11_v1.observation_worker.display.Display',return_value=connection) as opened:
            backend = open_readonly_backend(':pinned',{'app':20})
        opened.assert_called_once_with(':pinned')
        self.assertIs(backend.d,connection);self.assertIs(backend.root,root)
        self.assertIs(backend.targets['app'],window)
        self.assertFalse(hasattr(backend,'held_keycodes'))
        backend.close();self.assertEqual(calls,[('window',20),'closed'])
