import unittest
from presentation import Presentation

def observation(seq,focus=10):
    return dict(event='observation',id='p',step=0,sequence=seq,context=[['window',focus]],
                input_focus_before=focus,input_focus_after=focus,focus_samples_match=True)

class Tests(unittest.TestCase):
    def test_latest_is_flushed_before_result_without_duplicates(self):
        p=Presentation();p.project(dict(event='step_started',id='p',step=0,operation='settle'))
        first=observation(1);last=observation(2)
        self.assertEqual(p.project(first),[first]);self.assertEqual(p.project(last),[])
        result=dict(event='settle_result');self.assertEqual(p.project(result),[last,result])
        terminal=dict(event='terminal');self.assertEqual(p.project(terminal),[terminal])

    def test_transient_focus_change_is_forwarded(self):
        p=Presentation();p.project(dict(event='step_started',id='p',step=0,operation='settle'))
        for r in [observation(1),observation(2,20),observation(3)]:self.assertEqual(p.project(r),[r])

    def test_unknown_events_and_non_settle_observations_are_kept(self):
        p=Presentation()
        for r in [observation(1),observation(2),dict(event='critical_signal'),dict(event='rejected')]:
            self.assertEqual(p.project(r),[r])

    def test_failure_flushes_pending_image(self):
        p=Presentation();p.project(dict(event='step_started',id='p',step=0,operation='settle'))
        p.project(observation(1));p.project(observation(2))
        terminal=dict(event='terminal',status='expired')
        self.assertEqual(p.project(terminal),[observation(2),terminal])

if __name__=='__main__':unittest.main()
