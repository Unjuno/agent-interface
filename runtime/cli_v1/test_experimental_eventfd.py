"""Linux-only checks for the draft eventfd experiment, not a recovery proof."""
import os
import multiprocessing
import unittest
from unittest.mock import patch

from runtime.cli_v1.owned_guarded_session import _ExperimentalEventfd


def _child_after_parent_close(notifier, ready, proceed, result):
    try:
        ready.send('attached')
        proceed.recv()
        result.send(notifier.is_set())
    finally:
        notifier.close()


@unittest.skipUnless(hasattr(os, 'eventfd'), 'Linux eventfd required')
class ExperimentalEventfdTests(unittest.TestCase):
    def test_close_then_error_does_not_close_reused_fd(self):
        notifier=_ExperimentalEventfd();old_fd=notifier.fd
        replacement_read=replacement_write=None;installed=False
        real_close=os.close
        def close_then_raise(fd):
            real_close(fd)
            raise OSError('injected after close')
        try:
            replacement_read,replacement_write=os.pipe()
            with patch('runtime.cli_v1.owned_guarded_session.os.close', side_effect=close_then_raise):
                with self.assertRaises(OSError):notifier.close()
            self.assertEqual(notifier.close_status,'UNKNOWN')
            os.dup2(replacement_read,old_fd);installed=True
            notifier.close()
            os.write(replacement_write,b'x')
            self.assertEqual(os.read(old_fd,1),b'x')
        finally:
            try:
                notifier.close()
            finally:
                try:
                    if installed:real_close(old_fd)
                finally:
                    try:
                        if replacement_read is not None:real_close(replacement_read)
                    finally:
                        if replacement_write is not None:real_close(replacement_write)

    def test_close_error_keeps_unconfirmed_custody_visible(self):
        notifier=_ExperimentalEventfd()
        old_fd=notifier.fd
        try:
            with patch('runtime.cli_v1.owned_guarded_session.os.close',
                       side_effect=OSError('injected close failure')):
                with self.assertRaises(OSError):notifier.close()
            self.assertEqual(notifier.close_status, 'UNKNOWN')
        finally:
            os.close(old_fd)

    def test_parent_close_does_not_close_transferred_child_fd(self):
        context=multiprocessing.get_context('spawn')
        notifier=_ExperimentalEventfd()
        connections=[];child=None;started=False
        try:
            ready_r,ready_w=context.Pipe(False);connections.extend((ready_r,ready_w))
            proceed_r,proceed_w=context.Pipe(False);connections.extend((proceed_r,proceed_w))
            result_r,result_w=context.Pipe(False);connections.extend((result_r,result_w))
            child=context.Process(target=_child_after_parent_close,
                args=(notifier,ready_w,proceed_r,result_w))
            notifier.set();child.start();started=True
            self.assertTrue(ready_r.poll(3));self.assertEqual(ready_r.recv(),'attached')
            notifier.close()
            proceed_w.send('go')
            self.assertTrue(result_r.poll(3));self.assertTrue(result_r.recv())
            child.join(3);self.assertFalse(child.is_alive())
            self.assertEqual(child.exitcode,0)
        finally:
            try:
                if started:
                    if child.is_alive():child.kill()
                    child.join(3)
                    self.assertFalse(child.is_alive(),'fixture child cleanup failed')
            finally:
                try:
                    notifier.close()
                finally:
                    for conn in connections:conn.close()

    def test_managed_close_does_not_touch_reused_descriptor(self):
        notifier = _ExperimentalEventfd()
        old_fd = notifier.fd
        replacement_read = replacement_write = None
        installed = False
        try:
            replacement_read, replacement_write = os.pipe()
            notifier.close()
            os.dup2(replacement_read, old_fd)
            installed = True
            with self.assertRaises(OSError): notifier.is_set()
            with self.assertRaises(OSError): notifier.set()
            notifier.close()
            os.write(replacement_write, b'x')
            self.assertEqual(os.read(old_fd, 1), b'x')
        finally:
            try:
                notifier.close()
            finally:
                try:
                    if installed: os.close(old_fd)
                finally:
                    try:
                        if replacement_read is not None: os.close(replacement_read)
                    finally:
                        if replacement_write is not None: os.close(replacement_write)

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
