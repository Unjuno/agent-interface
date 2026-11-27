"""Timed UP remains finite when a process-identity read stalls; Fake X only."""
import time
import threading
import unittest
from test_input_owner_v12_process_identity import fixture

class TimedIdentityTests(unittest.TestCase):
    def test_no_new_focus_query_in_final_five_ms_and_post_release_check(self):
        with fixture() as (owner,lease,display,reader,events):
            lease.deadline=time.perf_counter_ns()+5_000_000_000
            lease.intent_token='quiet-boundary'
            lease.target_process_identity=(1,41,'a'*64,lease.deadline)
            deadline=[None];starts=[];delayed=[False]
            original=reader.focus
            def focus():
                now=time.perf_counter_ns();end=deadline[0]
                if end is not None:
                    starts.append(now)
                    remaining=end-now
                    if not delayed[0] and 5_000_000<remaining<12_000_000:
                        delayed[0]=True
                        time.sleep((remaining-4_000_000)/1e9)
                return original()
            reader.focus=focus
            admission=owner.call('down_timed',lease,{'key':'W','ticket':'quiet','duration_ms':200})
            deadline[0]=admission['timed_deadline_ns']
            limit=time.monotonic()+1
            while display.down and time.monotonic()<limit:time.sleep(.001)
            result=owner.call('take_timed_up',lease,'quiet')
            self.assertEqual(result['status'],'released')
            self.assertTrue(delayed[0])
            self.assertFalse([t for t in starts if deadline[0]-5_000_000<=t<deadline[0]],starts)
            self.assertTrue(any(t>=deadline[0] for t in starts),'post-release target check missing')

    def test_post_release_focus_change_cannot_be_reported_as_success(self):
        with fixture() as (owner,lease,display,reader,events):
            lease.deadline=time.perf_counter_ns()+5_000_000_000
            lease.intent_token='focus-after-release'
            lease.target_process_identity=(1,41,'a'*64,lease.deadline)
            deadline=[None];original=reader.focus
            def focus():
                if deadline[0] is not None and time.perf_counter_ns()>=deadline[0]-3_000_000:
                    return type('Focus',(),{'focus':42})()
                return original()
            reader.focus=focus
            admission=owner.call('down_timed',lease,{'key':'W','ticket':'changed','duration_ms':150})
            deadline[0]=admission['timed_deadline_ns']
            limit=time.monotonic()+1
            while display.down and time.monotonic()<limit:time.sleep(.001)
            result=owner.call('take_timed_up',lease,'changed')
            self.assertNotEqual(result['status'],'released')
            self.assertEqual(display.down,set())

    def test_focus_query_reaching_timed_deadline_retires_reader_and_releases(self):
        with fixture() as (owner,lease,display,reader,events):
            lease.deadline=time.perf_counter_ns()+5_000_000_000
            lease.intent_token='focus-deadline'
            lease.target_process_identity=(1,41,'a'*64,lease.deadline)
            entered=threading.Event();resume=threading.Event();block=threading.Event()
            original=reader.focus
            def focus():
                if block.is_set():
                    entered.set();resume.wait(2)
                return original()
            reader.focus=focus
            admission=owner.call('down_timed',lease,{'key':'W','ticket':'focus','duration_ms':250})
            block.set()
            try:
                self.assertTrue(entered.wait(1))
                end=time.monotonic()+1
                while display.down and time.monotonic()<end:time.sleep(.005)
                self.assertEqual(display.down,set())
                result=owner.call('take_timed_up',lease,'focus')
                self.assertNotEqual(result['status'],'released')
                release=next(row for row in owner.records if row.get('reason')=='target_query_invalidated')
                self.assertTrue(release['verified'])
                self.assertTrue(release['target_focus_query_failed'])
                attempt=next(iter(release['key_release_attempts'].values()))['attempts'][0]
                self.assertLessEqual(release['target_focus_query_failure']['finished_ns'],attempt['keymap_before_started_ns'])
                self.assertLessEqual(attempt['keymap_before_started_ns'],attempt['keymap_before_sampled_ns'])
                self.assertLessEqual(attempt['keymap_before_sampled_ns'],attempt['keyrelease_started_ns'])
                self.assertTrue(release['target_process_identity_reader']['retired'])
                detail=release['target_focus_query_failure']
                self.assertEqual(detail['deadline_ns'],admission['timed_deadline_ns'])
                self.assertLess(detail['started_ns'],detail['deadline_ns'])
                self.assertGreaterEqual(detail['finished_ns'],detail['deadline_ns'])
                self.assertEqual(detail['error_type'],'QueryUnavailable')
                self.assertGreaterEqual(release['key_release_intervals_ns'][0]['interval_ns'][0],admission['timed_deadline_ns'])
            finally:resume.set()
    def test_atomic_press_installs_deadline_before_later_identity_stall(self):
        with fixture() as (owner,lease,display,reader,events):
            lease.deadline=time.perf_counter_ns()+5_000_000_000
            lease.intent_token="atomic-identity"
            lease.target_process_identity=(1,41,"a"*64,lease.deadline)
            admission=owner.call("down_timed",lease,{"key":"W","ticket":"atomic","duration_ms":300})
            self.assertEqual(admission["timed_deadline_ns"],admission["input_ack_ns"]+300_000_000)
            reader.entered.clear();reader.block=True
            self.assertTrue(reader.entered.wait(1))
            try:
                limit=time.monotonic()+.6
                while display.down and time.monotonic()<limit:time.sleep(.005)
                self.assertEqual(display.down,set(),"atomic timed release waited behind the identity query")
                self.assertNotEqual(owner.call("take_timed_up",lease,"atomic")["status"],"released")
                release=next(row for row in owner.records if row.get("reason")=="target_generation_invalidated")
                detail=release["target_identity_query_failure"]
                self.assertEqual(detail["operation"],"process_identity")
                self.assertEqual(detail["deadline_ns"],admission["timed_deadline_ns"])
                self.assertLess(detail["started_ns"],detail["deadline_ns"])
                self.assertGreaterEqual(detail["finished_ns"],detail["deadline_ns"])
                self.assertEqual(detail["error_type"],"QueryUnavailable")
                self.assertLessEqual(detail["finished_ns"],release["key_release_intervals_ns"][0]["interval_ns"][0])
            finally:reader.resume.set()
    def test_stalled_identity_read_does_not_hide_hold_deadline(self):
        with fixture() as (owner,lease,display,reader,events):
            lease.deadline=time.perf_counter_ns()+5_000_000_000
            lease.intent_token="identity-timed"
            lease.target_process_identity=(1,41,"a"*64,lease.deadline)
            owner.call("down",lease,"W")
            deadline=time.perf_counter_ns()+300_000_000
            owner.call("arm_timed_up",lease,{"ticket":"t","keys":["W"],"deadline_ns":deadline})
            reader.entered.clear();reader.block=True
            self.assertTrue(reader.entered.wait(1))
            try:
                limit=time.monotonic()+.6
                while display.down and time.monotonic()<limit:time.sleep(.005)
                self.assertEqual(display.down,set(),"timed release waited behind the identity query")
                result=owner.call("take_timed_up",lease,"t")
                self.assertNotEqual(result["status"],"released", "identity timeout cannot claim normal timed completion")
            finally:reader.resume.set()


class TimedDeadlineBoundaryDecisionTests(unittest.TestCase):
    def test_due_timed_release_never_starts_a_new_focus_query(self):
        from types import SimpleNamespace
        import threading
        from input_owner_v12 import _defer_timed_focus_query
        lease=SimpleNamespace(deadline=200_000_000,cancel=threading.Event())
        timed={'status':'armed','lease':lease,'deadline_ns':100_000_000}
        reader=object()
        self.assertFalse(_defer_timed_focus_query(lease,reader,timed,94_999_999))
        self.assertTrue(_defer_timed_focus_query(lease,reader,timed,95_000_000))
        self.assertTrue(_defer_timed_focus_query(lease,reader,timed,100_000_000))
        self.assertTrue(_defer_timed_focus_query(lease,reader,timed,100_000_001))
        self.assertFalse(_defer_timed_focus_query(lease,reader,timed,200_000_000))
        lease.cancel.set()
        self.assertFalse(_defer_timed_focus_query(lease,reader,timed,99_000_000))
        lease.cancel.clear()
        self.assertFalse(_defer_timed_focus_query(lease,None,timed,99_000_000))
        other=SimpleNamespace(deadline=200_000_000,cancel=threading.Event())
        self.assertFalse(_defer_timed_focus_query(other,reader,timed,99_000_000))
        timed['status']='released'
        self.assertFalse(_defer_timed_focus_query(lease,reader,timed,99_000_000))

if __name__=="__main__":unittest.main()
