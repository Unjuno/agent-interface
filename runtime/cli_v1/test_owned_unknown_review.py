import unittest

from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner


class OwnedUnknownReviewTests(unittest.TestCase):
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
