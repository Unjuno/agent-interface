import threading
import time
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from .target_queries import QueryUnavailable, TargetQueryWorker, X11TargetQueries, focus_within_target
from .process_identity import process_generation_from_identity,process_incarnation_from_identity

_PID,_START_TICKS=4321,98765


def process_details(xid, incarnation=None):
    return {'xid':xid,'pid':_PID,'start_ticks':_START_TICKS,
        'process_generation':process_generation_from_identity(xid,_PID,_START_TICKS),
        'process_incarnation':(incarnation or
            process_incarnation_from_identity(_PID,_START_TICKS))}


class QueryWorkerTests(unittest.TestCase):
    def test_windows_for_process_returns_only_viewable_xres_owned_descendants(self):
        from Xlib import X
        reader = object.__new__(X11TargetQueries)
        windows = {
            21:SimpleNamespace(id=21,get_attributes=lambda:SimpleNamespace(map_state=X.IsViewable),
                query_tree=lambda:SimpleNamespace(children=[])),
            22:SimpleNamespace(id=22,get_attributes=lambda:SimpleNamespace(map_state=X.IsUnmapped),
                query_tree=lambda:SimpleNamespace(children=[])),
            23:SimpleNamespace(id=23,get_attributes=lambda:SimpleNamespace(map_state=X.IsViewable),
                query_tree=lambda:SimpleNamespace(children=[])),
        }
        reader.connection = SimpleNamespace(
            screen=lambda:SimpleNamespace(root=SimpleNamespace(query_tree=lambda:
                SimpleNamespace(children=[SimpleNamespace(id=xid) for xid in windows]))),
            create_resource_object=lambda _kind,xid:windows[xid])
        metadata = {'schema':'agent-interface/x11-window-metadata-cues-v1',
            'mapped':True,'input_authority':False,'authenticated_role':False}
        with patch('runtime.guarded_x11_v1.target_queries.read_linux_x11_process_identity_details',
                   side_effect=[process_details(21),process_details(23, 'd'*64)]), \
             patch.object(reader,'_bounded_text_property',side_effect=lambda window,_name:
                   'task-artifact.fods - LibreOffice Calc' if window.id != 22 else 'unrelated'), \
             patch.object(reader,'_window_metadata',side_effect=lambda xid:
                   dict(metadata,xid=xid,process_pid=_PID)) as window_metadata:
            rows=reader.read('windows_for_process',
                {'pid':_PID,'title_hint':'task-artifact.fods'})
        self.assertEqual([row['xid'] for row in rows],[21,23])
        self.assertEqual(window_metadata.call_args_list,[unittest.mock.call(21),
                                                         unittest.mock.call(23)])
        self.assertTrue(all(row['input_authority'] is False for row in rows))
        with self.assertRaisesRegex(ValueError,'exact PID and title hint'):
            reader.read('windows_for_process',_PID)

    def test_windows_for_process_refuses_unbounded_descendant_tree(self):
        reader=object.__new__(X11TargetQueries)
        root=SimpleNamespace(query_tree=lambda:SimpleNamespace(
            children=[SimpleNamespace(id=2)]))
        reader.connection=SimpleNamespace(
            screen=lambda:SimpleNamespace(root=root),
            create_resource_object=lambda _kind,_xid:SimpleNamespace(
                get_attributes=lambda:SimpleNamespace(map_state=0),
                query_tree=lambda:SimpleNamespace(
                    children=[SimpleNamespace(id=xid) for xid in range(3,4101)])))
        with self.assertRaisesRegex(QueryUnavailable,'enumeration limit'):
            reader.read('windows_for_process',
                {'pid':_PID,'title_hint':'task-artifact.fods'})

    def test_windows_for_process_rechecks_pid_after_metadata_boundary(self):
        from Xlib import X
        reader=object.__new__(X11TargetQueries)
        window=SimpleNamespace(get_attributes=lambda:SimpleNamespace(map_state=X.IsViewable),
            query_tree=lambda:SimpleNamespace(children=[]))
        reader.connection=SimpleNamespace(
            screen=lambda:SimpleNamespace(root=SimpleNamespace(query_tree=lambda:
                SimpleNamespace(children=[SimpleNamespace(id=21)]))),
            create_resource_object=lambda _kind,_xid:window)
        changed={'process_pid':_PID+1}
        with patch('runtime.guarded_x11_v1.target_queries.read_linux_x11_process_identity_details',
                   return_value=process_details(21)), \
             patch.object(reader,'_bounded_text_property',return_value='task-artifact.fods'), \
             patch.object(reader,'_window_metadata',return_value=changed):
            with self.assertRaisesRegex(QueryUnavailable,'process changed'):
                reader.read('windows_for_process',
                    {'pid':_PID,'title_hint':'task-artifact.fods'})

    def test_windows_for_process_uses_window_manager_ancestor_title_as_cue(self):
        from Xlib import X
        reader=object.__new__(X11TargetQueries)
        windows={
            21:SimpleNamespace(id=21,
                get_attributes=lambda:SimpleNamespace(map_state=X.IsViewable),
                query_tree=lambda:SimpleNamespace(children=[SimpleNamespace(id=22)])),
            22:SimpleNamespace(id=22,
                get_attributes=lambda:SimpleNamespace(map_state=X.IsViewable),
                query_tree=lambda:SimpleNamespace(children=[])),
        }
        reader.connection=SimpleNamespace(
            screen=lambda:SimpleNamespace(root=SimpleNamespace(query_tree=lambda:
                SimpleNamespace(children=[SimpleNamespace(id=21)]))),
            create_resource_object=lambda _kind,xid:windows[xid])
        metadata={'schema':'agent-interface/x11-window-metadata-cues-v1',
            'mapped':True,'input_authority':False,'authenticated_role':False,
            'process_pid':_PID,'xid':22}
        with patch('runtime.guarded_x11_v1.target_queries.read_linux_x11_process_identity_details',
                   side_effect=[dict(process_details(21),pid=_PID+1),
                                process_details(22)]), \
             patch.object(reader,'_bounded_text_property',
                   side_effect=lambda window,_name:
                       'task-artifact.fods - LibreOffice Calc' if window.id==21 else None), \
             patch.object(reader,'_window_metadata',return_value=dict(metadata)):
            rows=reader.read('windows_for_process',
                {'pid':_PID,'title_hint':'task-artifact.fods'})
        self.assertEqual([row['xid'] for row in rows],[22])
        self.assertEqual(rows[0]['discovery_title_xid'],21)
        self.assertFalse(rows[0]['input_authority'])

    def test_process_incarnation_dispatch_uses_isolated_xres_reader(self):
        reader = object.__new__(X11TargetQueries)
        reader.connection = object()
        with patch('runtime.guarded_x11_v1.target_queries.read_linux_x11_process_identity_details',
                   return_value=process_details(21,'b'*64)) as incarnation:
            self.assertEqual(reader.read('process_incarnation', 21), 'b'*64)
        incarnation.assert_called_once_with(reader.connection, 21)

    def test_window_metadata_is_bounded_read_only_cue_and_rechecks_focus_and_incarnation(self):
        from Xlib import X, Xatom
        reader = object.__new__(X11TargetQueries)
        window = SimpleNamespace(
            get_attributes=lambda:SimpleNamespace(map_state=X.IsViewable),
            query_tree=lambda:SimpleNamespace(parent=SimpleNamespace(id=10)),
            get_property=lambda atom, _type, _offset, _length: {
                'WM_TRANSIENT_FOR':SimpleNamespace(property_type=Xatom.WINDOW,
                    format=32,bytes_after=0,value=[20]),
                'WM_CLASS':SimpleNamespace(format=8,bytes_after=0,
                    property_type=Xatom.STRING,value=b'soffice\0LibreOffice\0'),
                '_NET_WM_NAME':SimpleNamespace(format=8,bytes_after=0,
                    property_type='UTF8_STRING',value=b'Save As'),
                'WM_WINDOW_ROLE':SimpleNamespace(format=8,bytes_after=0,
                    property_type=Xatom.STRING,value=b'file-chooser')
            }.get(atom))
        reader.connection = SimpleNamespace(
            create_resource_object=lambda kind, xid: window,
            intern_atom=lambda name: name)
        reader._window_incarnation = Mock(side_effect=['a'*64,'a'*64])
        with patch('runtime.guarded_x11_v1.target_queries.read_linux_x11_process_identity_details',
                   side_effect=[process_details(21,'b'*64),
                                process_details(21,'b'*64)]) as process_identity, \
             patch('runtime.guarded_x11_v1.target_queries.focus_within_target',
                   side_effect=[True,True]) as focus:
            result = reader.read('window_metadata',21)
        self.assertEqual(result['schema'],'agent-interface/x11-window-metadata-cues-v1')
        self.assertEqual(result['xid'],21)
        self.assertEqual(result['parent_xid'],10)
        self.assertEqual(result['transient_for_xid'],20)
        self.assertEqual(result['wm_class'],['soffice','LibreOffice'])
        self.assertEqual((result['title_cue'],result['role_cue']),
                         ('Save As','file-chooser'))
        self.assertEqual(result['process_incarnation'],'b'*64)
        self.assertEqual(result['process_pid'],_PID)
        self.assertEqual(result['process_start_ticks'],_START_TICKS)
        self.assertEqual(result['process_generation'],
            process_generation_from_identity(21,_PID,_START_TICKS))
        self.assertTrue(result['focused_before'] and result['focused_after'])
        self.assertFalse(result['input_authority'])
        self.assertFalse(result['authenticated_role'])
        self.assertEqual(focus.call_count,2)
        self.assertEqual(process_identity.call_count,2)

        for incarnations, processes in (
                (['a'*64,'d'*64],[process_details(21,'b'*64),
                                  process_details(21,'b'*64)]),
                (['a'*64,'a'*64],[process_details(21,'b'*64),
                                  process_details(21,'e'*64)])):
            with self.subTest(incarnations=incarnations,processes=processes):
                changed = object.__new__(X11TargetQueries)
                changed.connection = reader.connection
                changed._window_incarnation = Mock(side_effect=incarnations)
                with patch('runtime.guarded_x11_v1.target_queries.read_linux_x11_process_identity_details',
                           side_effect=processes), \
                     patch('runtime.guarded_x11_v1.target_queries.focus_within_target',
                           side_effect=[True,True]):
                    with self.assertRaises(QueryUnavailable):
                        changed.read('window_metadata',21)

    def test_window_metadata_refuses_oversized_or_malformed_properties(self):
        reader = object.__new__(X11TargetQueries)
        reader.connection = SimpleNamespace(intern_atom=lambda name: name)
        window = SimpleNamespace(get_property=lambda *_:SimpleNamespace(
            property_type='UTF8_STRING',format=8,bytes_after=0,value=b'x'*257))
        with self.assertRaises(QueryUnavailable):
            reader._bounded_text_property(window,'_NET_WM_NAME')

    def test_window_metadata_refuses_truncated_property_without_fetching_remainder(self):
        reader = object.__new__(X11TargetQueries)
        reader.connection = SimpleNamespace(intern_atom=lambda name: name)
        read = Mock(return_value=SimpleNamespace(property_type='UTF8_STRING',
            format=8,bytes_after=4096,value=b'x'*256))
        window = SimpleNamespace(get_property=read)
        with self.assertRaises(QueryUnavailable):
            reader._bounded_text_property(window,'_NET_WM_NAME')
        read.assert_called_once_with('_NET_WM_NAME',unittest.mock.ANY,0,64)

    def test_delayed_read_hook_retires_and_quarantines_without_starting_late_query(self):
        entered, resume, closed = threading.Event(), threading.Event(), threading.Event()
        reader = SimpleNamespace(read=Mock(return_value=True), close=closed.set)
        def before_read(operation, xid):
            self.assertEqual((operation, xid), ('focus', 20))
            entered.set()
            resume.wait(2)
        worker = TargetQueryWorker(lambda: reader, before_read=before_read)
        result = []
        def invoke():
            try:
                result.append(worker.read('focus', 20,
                    deadline_ns=time.monotonic_ns()+80_000_000,
                    cancelled=lambda: False))
            except QueryUnavailable:
                result.append('retired')
        caller = threading.Thread(target=invoke)
        caller.start()
        try:
            self.assertTrue(entered.wait(1))
            caller.join(1)
            self.assertFalse(caller.is_alive())
            self.assertEqual(result, ['retired'])
            self.assertTrue(worker.snapshot()['retired'])
            self.assertTrue(worker.snapshot()['pending'])
            self.assertTrue(worker.snapshot()['thread_alive'])
            resume.set()
            self.assertTrue(closed.wait(1))
            worker.thread.join(1)
            self.assertFalse(worker.snapshot()['pending'])
            self.assertFalse(worker.snapshot()['thread_alive'])
            reader.read.assert_not_called()
        finally:
            resume.set()
            worker.close()
            caller.join(2)

    def test_focus_transport_failure_retires_reader_but_legacy_helper_refuses(self):
        closed = threading.Event()
        connection = SimpleNamespace(get_input_focus=Mock(side_effect=OSError('transport failed')),
                                     close=closed.set)
        self.assertIs(focus_within_target(connection,20),False)
        with patch('runtime.guarded_x11_v1.target_queries.display.Display',return_value=connection):
            worker = TargetQueryWorker(lambda:X11TargetQueries(':fixed'))
            try:
                with self.assertRaises(QueryUnavailable):
                    worker.read('focus',20,deadline_ns=time.monotonic_ns()+1_000_000_000,cancelled=lambda:False)
                self.assertTrue(worker.snapshot()['retired'])
            finally: worker.close()
            self.assertTrue(closed.wait(2))

    def test_cancelled_open_closes_without_starting_another_query(self):
        entered,resume,closed,cancel = [threading.Event() for _ in range(4)]
        reader = SimpleNamespace(read=Mock(return_value=True),close=closed.set)
        results = []
        def factory():
            entered.set();resume.wait(3);return reader
        worker = TargetQueryWorker(factory)
        def invoke():
            try: results.append(worker.read('focus',20,deadline_ns=time.monotonic_ns()+2_000_000_000,cancelled=cancel.is_set))
            except QueryUnavailable: results.append('refused')
        caller = threading.Thread(target=invoke)
        caller.start()
        try:
            self.assertTrue(entered.wait(1));cancel.set();caller.join(1)
            self.assertFalse(caller.is_alive());self.assertEqual(results,['refused'])
            self.assertTrue(worker.snapshot()['retired'])
            resume.set();self.assertTrue(closed.wait(1))
            reader.read.assert_not_called()
        finally:
            cancel.set();resume.set();worker.close();caller.join(2)

    def test_readonly_protocol_client_and_close_share_worker_thread(self):
        ids, closed = [], threading.Event()
        connection = SimpleNamespace(
            get_input_focus=lambda:ids.append(threading.get_ident()) or SimpleNamespace(focus=SimpleNamespace(id=20)),
            close=lambda:ids.append(threading.get_ident()) or closed.set())
        with patch('runtime.guarded_x11_v1.target_queries.display.Display',return_value=connection) as opened, \
                patch('runtime.guarded_x11_v1.target_queries.read_linux_x11_process_identity_details',
                      return_value=process_details(20)) as identity:
            worker = TargetQueryWorker(lambda:X11TargetQueries(':frozen-name'))
            try:
                self.assertIs(worker.read('focus',20,deadline_ns=time.monotonic_ns()+1_000_000_000,cancelled=lambda:False),True)
                self.assertEqual(worker.read('focus_id',20,deadline_ns=time.monotonic_ns()+1_000_000_000,cancelled=lambda:False),20)
                self.assertEqual(worker.read('process_identity',20,deadline_ns=time.monotonic_ns()+1_000_000_000,cancelled=lambda:False),
                    process_generation_from_identity(20,_PID,_START_TICKS))
            finally: worker.close()
            self.assertTrue(closed.wait(2))
            opened.assert_called_once_with(':frozen-name')
            identity.assert_called_once_with(connection,20)
            self.assertEqual(len(set(ids)),1)
            self.assertNotIn(threading.get_ident(),ids)

    def test_close_before_start_and_expired_request_create_no_thread(self):
        for close_first in (False,True):
            factory = Mock()
            worker = TargetQueryWorker(factory)
            if close_first: worker.close()
            with self.assertRaises(QueryUnavailable):
                worker.read('focus',20,deadline_ns=0,cancelled=lambda:False)
            factory.assert_not_called()
            self.assertFalse(worker.snapshot()['thread_alive'])

    def test_cancelled_pending_request_discards_late_value_and_never_reopens(self):
        entered,resume,closed,cancel = [threading.Event() for _ in range(4)]
        results = []
        class Reader:
            def read(self,operation,xid):
                entered.set();resume.wait(3);return 'late'
            def close(self): closed.set()
        factory = Mock(return_value=Reader())
        worker = TargetQueryWorker(factory)
        def invoke():
            try: results.append(worker.read('focus',20,deadline_ns=time.monotonic_ns()+2_000_000_000,cancelled=cancel.is_set))
            except QueryUnavailable: results.append('refused')
        caller = threading.Thread(target=invoke)
        caller.start()
        try:
            self.assertTrue(entered.wait(1));cancel.set();caller.join(1)
            self.assertFalse(caller.is_alive());self.assertEqual(results,['refused'])
            self.assertTrue(worker.snapshot()['retired']);self.assertTrue(worker.snapshot()['pending'])
            resume.set();self.assertTrue(closed.wait(1))
            with self.assertRaises(QueryUnavailable):
                worker.read('focus',20,deadline_ns=time.monotonic_ns()+1_000_000_000,cancelled=lambda:False)
            factory.assert_called_once()
        finally:
            cancel.set();resume.set();worker.close();caller.join(2)

    def test_query_failure_remains_a_failure_and_closes_client(self):
        closed = threading.Event()
        reader = SimpleNamespace(read=Mock(side_effect=OSError('query unavailable')),close=closed.set)
        worker = TargetQueryWorker(lambda:reader)
        with self.assertRaises(QueryUnavailable):
            worker.read('process_identity',20,deadline_ns=time.monotonic_ns()+1_000_000_000,cancelled=lambda:False)
        self.assertTrue(closed.wait(2));self.assertTrue(worker.snapshot()['retired'])
