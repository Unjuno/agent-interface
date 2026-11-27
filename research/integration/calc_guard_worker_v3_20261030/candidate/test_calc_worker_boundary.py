import tempfile,threading,time,unittest
from types import SimpleNamespace
from unittest.mock import patch
from Xlib import X
from PIL import Image
from runtime.cli_v1.test_mcp_process_identity import FakeX
from runtime.guarded_x11_v1.bridge import NativeHandleBridge
from runtime.guarded_x11_v1.test_observation_worker import reader_backend

class CalcWorkerBoundaryTests(unittest.TestCase):
    def exercise(self,boundary,trigger):
        from runtime.guarded_x11_v1.observation_worker import X11ObservationReader
        from save_guard import SemanticSaveGuard
        from composition import CalcComposition
        fake = FakeX(self)
        focus = [20]
        if trigger=='pure_changed':
            old_emit=fake.emit
            def changed_emit(display,kind,code):
                old_emit(display,kind,code)
                if kind==X.KeyPress and code==1:
                    pixels=Image.frombytes('RGB',(32,32),fake.raw,'raw','BGRX')
                    pixels.putpixel((31,31),(255,0,0));fake.raw=pixels.tobytes('raw','BGRX')
            event_patch=patch('runtime.backends.x11_v1.backend.xtest.fake_input',side_effect=changed_emit)
            event_patch.start();self.addCleanup(event_patch.stop)
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
        guard_ref={}
        def verify(stage,source,image):
            reader_threads.append(threading.get_ident())
            if boundary=='callback' and 1 in fake.down: gate()
            if trigger in ('pure','pure_cancel','pure_changed','pure_expired'): return guard_ref['composition'].guard_perceive(source,image)['cells_filled'] is True
            guard_ref['guard'].validate(stage)
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
            guard=SemanticSaveGuard(bridge,alias='field',offset=offset,regions=[[31,31,32,32]],deadline_ns=now[0]+5_000_000_000,clock=lambda:now[0])
            guard.arm(source,bridge.history[source['sequence']][1],cue_record={'cue':'filled','sequence':source['sequence'],'artifact_sha256':source['native']['artifact']['sha256']})
            guard_ref['guard']=guard
            if trigger=='pure_expired': guard.deadline_ns=now[0]
            c=CalcComposition.__new__(CalcComposition);c.bridge=bridge;c.guard=guard
            c.refs={'context_region':[0,0,1,1],'save_alias':'field'}
            c.context_pixels=bridge.history[source['sequence']][1].crop(c.refs['context_region']).tobytes()
            guard_ref['composition']=c
            tail = [{'op':'key_chord','keys':['CTRL','a']}]
            def invoke():
                try:
                    with bridge.cancellation_scope('only-call'),bridge.input_guard('field',offset,tail=tail,verify=verify):
                        results.append(bridge.keyboard('field',offset,tail=tail))
                except BaseException as error: errors.append(error)
            worker = threading.Thread(target=invoke)
            worker.start()
            try:
                if trigger=='pure_cancel':
                    self.assertTrue(entered.wait(2),(results,errors))
                    self.assertEqual(fake.down,{1})
                    self.assertEqual(bridge.request_cancel('only-call')['status'],'cancel_requested')
                    worker.join(2)
                    self.assertFalse(worker.is_alive())
                    self.assertEqual(errors,[])
                    self.assertEqual(results[0]['status'],'execution_failed')
                    self.assertTrue(results[0]['execution']['releases'][-1]['verified'])
                    self.assertEqual(fake.emissions,[(X.KeyPress,1),(X.KeyRelease,1)])
                    self.assertEqual(fake.down,set())
                    self.assertTrue(bridge._observations.snapshot()['retired'])
                    self.assertFalse(resume.is_set())
                    resume.set();self.assertTrue(closed.wait(2))
                    return
                worker.join(2)
                self.assertFalse(worker.is_alive())
                self.assertEqual(errors,[])
                if trigger=='pure_expired':
                    self.assertEqual(results[0]['status'],'refused',results)
                    self.assertIs(results[0]['input_dispatched'],False)
                    self.assertEqual(fake.emissions,[])
                    self.assertEqual(fake.down,set())
                    return
                if trigger=='pure_changed':
                    self.assertEqual(results[0]['status'],'execution_failed',results)
                    self.assertTrue(results[0]['execution']['releases'][-1]['verified'])
                    self.assertEqual(fake.emissions,[(X.KeyPress,1),(X.KeyRelease,1)])
                    self.assertEqual(fake.down,set())
                    return
                if trigger=='pure':
                    self.assertEqual(results[0]['status'],'completed',results)
                    self.assertEqual(fake.down,set())
                    return
                self.assertEqual(results[0]['status'],'refused')
                self.assertIs(results[0]['input_dispatched'],False)
                self.assertEqual(fake.emissions,[])
                self.assertEqual(fake.down,set())
                self.assertTrue(bridge.review_required)
                self.assertTrue(bridge._observations.snapshot()['retired'])
                self.assertIn('isolated visual check unavailable',results[0]['error'])
            finally:
                resume.set();worker.join(5);bridge.close()

    def test_nested_binding_query_refuses_without_input(self): self.exercise('healthy','none')
    def test_capture_only_guard_succeeds_with_worker(self): self.exercise('healthy','pure')
    def test_capture_only_guard_cancel_during_control(self): self.exercise('callback','pure_cancel')
    def test_capture_only_guard_changed_cell_stops_suffix(self): self.exercise('healthy','pure_changed')
    def test_capture_only_guard_expired_refuses_input(self): self.exercise('healthy','pure_expired')
