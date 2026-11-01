"""Linux-only checks for the draft eventfd experiment, not a recovery proof."""
import os
import unittest

from runtime.cli_v1.owned_guarded_session import _ExperimentalEventfd


@unittest.skipUnless(hasattr(os, 'eventfd'), 'Linux eventfd required')
class ExperimentalEventfdTests(unittest.TestCase):
    def test_readability_changes_after_signal(self):
        notifier = _ExperimentalEventfd()
        try:
            self.assertFalse(notifier.is_set())
            notifier.set()
            self.assertTrue(notifier.is_set())
        finally:
            os.close(notifier.fd)

    def test_invalid_fd_is_error_not_successful_revocation(self):
        notifier = _ExperimentalEventfd()
        os.close(notifier.fd)
        with self.assertRaises(OSError):
            notifier.is_set()

    def test_reused_fd_cannot_impersonate_original_eventfd(self):
        notifier = _ExperimentalEventfd()
        replacement_read = replacement_write = None
        original_open = True
        try:
            replacement_read, replacement_write = os.pipe()
            os.close(notifier.fd)
            original_open = False
            os.dup2(replacement_read, notifier.fd)
            original_open = True
            with self.assertRaises(OSError):
                notifier.is_set()
        finally:
            try:
                if original_open:
                    os.close(notifier.fd)
            finally:
                try:
                    if replacement_read is not None:
                        os.close(replacement_read)
                finally:
                    if replacement_write is not None:
                        os.close(replacement_write)


if __name__ == '__main__':
    unittest.main()
