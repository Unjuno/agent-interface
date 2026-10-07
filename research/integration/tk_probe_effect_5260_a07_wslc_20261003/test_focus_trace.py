import unittest
from focus_trace import FocusTrace


class FocusTraceTests(unittest.TestCase):
    def test_memory_only_has_zero_file_calls(self):
        writes=[];tick=iter(range(100,1000))
        trace=FocusTrace('MEMORY_ONLY',lambda n,v:writes.append((n,v)),lambda:next(tick))
        trace.record('FocusIn','target',{'token':'fresh','pid':17,'target_id':42})
        self.assertEqual(writes,[])
        self.assertEqual(len(trace.events),1)
        self.assertEqual(trace.publications,[])
        callback=trace.snapshot()['callbacks'][0]
        self.assertEqual(callback['event_sequence'],1)
        self.assertEqual(callback['started_ns'],trace.events[0]['monotonic_ns'])
        self.assertGreater(callback['completed_record_ns'],callback['started_ns'])

    def test_sync_file_traces_are_bound_to_write_and_event(self):
        writes=[];tick=iter(range(100,1000))
        trace=FocusTrace('SYNC_FILE',lambda n,v:writes.append((n,v)),lambda:next(tick))
        trace.record('FocusIn','target',{'token':'fresh','pid':17,'target_id':42})
        self.assertEqual([name for name,_ in writes],['focus_state.json','focus_ack.json'])
        self.assertEqual(len(trace.publications),2)
        self.assertGreaterEqual(trace.snapshot()['callbacks'][0]['completed_record_ns'],
                                trace.publications[-1]['completed_ns'])
        for publication in trace.publications:
            self.assertLessEqual(publication['started_ns'],publication['completed_ns'])
            self.assertEqual(publication['event_sequence'],1)

    def test_copied_snapshot_cannot_be_changed_by_later_events(self):
        writes=[];tick=iter(range(100,1000))
        trace=FocusTrace('SYNC_FILE',lambda n,v:writes.append((n,v)),lambda:next(tick))
        trace.record('FocusIn','target',{'token':'fresh','pid':17,'target_id':42})
        snapshot=trace.snapshot()
        trace.record('FocusOut','target',{'token':'fresh','pid':17,'target_id':42})
        self.assertEqual(len(snapshot['events']),1)
        self.assertEqual(snapshot['last_state']['widget'],'target')
        self.assertEqual(trace.snapshot()['last_state']['widget'],'none')
        writes[0][1]['widget']='tampered'
        self.assertEqual(snapshot['last_state']['widget'],'target')

    def test_unknown_mode_refused_before_a_file_call(self):
        writes=[]
        with self.assertRaises(ValueError):
            FocusTrace('UNKNOWN',lambda n,v:writes.append(n))
        self.assertEqual(writes,[])

    def test_write_failure_retained_without_retry_or_false_publication(self):
        writes=[]
        def fail(name,value):
            writes.append(name)
            raise OSError('construction disk failure')
        trace=FocusTrace('SYNC_FILE',fail)
        with self.assertRaises(OSError):
            trace.record('FocusIn','target',{'token':'fresh','pid':17,'target_id':42})
        self.assertEqual(writes,['focus_state.json'])
        self.assertEqual(trace.publications,[])
        self.assertEqual(len(trace.events),1)


if __name__=='__main__':unittest.main()
