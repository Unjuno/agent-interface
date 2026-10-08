import os
from pathlib import Path
import unittest
from private_cache import PrivateCache

class PrivateCacheTests(unittest.TestCase):
    def test_owned_writable_cache_has_copied_binding_and_bounded_cleanup(self):
        cache=PrivateCache('fresh-row')
        receipt=cache.snapshot()
        try:
            path=Path(receipt['path'])
            self.assertTrue(path.is_dir())
            self.assertEqual(receipt['token'],'fresh-row')
            self.assertEqual(cache.environment({'DISPLAY':':97'})['XDG_CACHE_HOME'],str(path))
            self.assertEqual(cache.environment({'DISPLAY':':97'})['DISPLAY'],':97')
            (path/'unit-file').write_bytes(b'exact')
            receipt['token']='tampered'
            self.assertEqual(cache.snapshot()['token'],'fresh-row')
            self.assertEqual(receipt['mode'],0o700 if os.name=='posix' else receipt['mode'])
        finally:cache.cleanup()
        final=cache.snapshot()
        self.assertFalse(Path(final['path']).exists())
        self.assertTrue(final['removed'])
        self.assertGreaterEqual(final['cleanup_finished_ns'],final['created_ns'])

    def test_two_rows_do_not_reuse_cache_and_cleanup_is_once(self):
        first=PrivateCache('first');second=PrivateCache('second')
        try:self.assertNotEqual(first.snapshot()['path'],second.snapshot()['path'])
        finally:first.cleanup();second.cleanup()
        with self.assertRaises(RuntimeError):first.cleanup()

if __name__=='__main__':unittest.main()

