import unittest
import threading
from unittest.mock import Mock

from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner


class OwnedUnknownReviewTests(unittest.TestCase):
    def test_late_success_cannot_erase_concurrent_notification_failure(self):
        owner = OwnedGuardedSessionOwner({'app': 1}, '/tmp/owned-unknown-review')
        entered=threading.Event();resume=threading.Event()
        def signal():
            if threading.current_thread().name == 'first':
                entered.set()
                if not resume.wait(2):raise RuntimeError('fixture timeout')
            else:
                raise OSError('injected')
        owner._unknown_event=Mock();owner._unknown_event.set.side_effect=signal
        thread=threading.Thread(target=lambda:setattr(owner,'_execution_unknown',True),name='first')
        thread.start()
        try:
            self.assertTrue(entered.wait(1))
            owner._execution_unknown=True
        finally:
            resume.set();thread.join(2)
        self.assertFalse(thread.is_alive())
        self.assertEqual(owner.snapshot()['unknown_notification']['status'],'failed')

    def test_failed_notification_preserves_parent_unknown_and_reports_failure(self):
        owner = OwnedGuardedSessionOwner({'app': 1}, '/tmp/owned-unknown-review')
        owner._unknown_event = Mock()
        owner._unknown_event.set.side_effect = OSError('injected notification failure')
        owner._execution_unknown = True
        self.assertTrue(owner._execution_unknown)
        self.assertTrue(owner.snapshot()['review_required'])
        self.assertEqual(owner.snapshot()['cleanup_status'], 'UNKNOWN')
        self.assertEqual(owner.snapshot()['unknown_notification']['status'], 'failed')
        self.assertEqual(owner.snapshot()['unknown_notification']['error_type'], 'OSError')
        owner._unknown_event.set.side_effect = None
        owner._execution_unknown = True
        self.assertEqual(owner.snapshot()['unknown_notification']['status'], 'failed')

    def test_stale_child_snapshot_cannot_clear_parent_unknown_review(self):
        owner = OwnedGuardedSessionOwner({'app': 1}, '/tmp/owned-unknown-review')
        owner._execution_unknown = True
        owner.review_required = True
        owner._apply_snapshot({'review_required': False})
        self.assertTrue(owner.snapshot()['review_required'])
        self.assertEqual(owner.snapshot()['cleanup_status'], 'UNKNOWN')

    def test_known_parent_accepts_child_review_completion(self):
        owner = OwnedGuardedSessionOwner({'app': 1}, '/tmp/owned-unknown-review')
        owner.review_required = True
        owner._apply_snapshot({'review_required': False})
        self.assertFalse(owner.snapshot()['review_required'])


if __name__ == '__main__':
    unittest.main()
