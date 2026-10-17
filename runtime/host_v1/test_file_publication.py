"""Post-link publication failures keep an occupied, complete receipt slot."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from runtime.host_v1.file_publication import publish


@unittest.skipUnless(hasattr(os, 'O_DIRECTORY'), 'directory fsync requires O_DIRECTORY')
class PublicationFailureTests(unittest.TestCase):
    def test_directory_fsync_failure_preserves_complete_slot_and_forbids_republish(self):
        with tempfile.TemporaryDirectory(prefix='host-publication-postlink-') as directory:
            slot = Path(directory) / 'request.json'
            value = {'id': 1, 'tool': 'interface_guarded_input', 'arguments': {'alias': 'save'}}
            expected = (json.dumps(value, sort_keys=True, allow_nan=False) + '\n').encode('utf-8')
            original_fsync = os.fsync
            calls = 0

            def fail_directory_sync(fd):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError('injected directory fsync failure')
                return original_fsync(fd)

            with patch('runtime.host_v1.file_publication.os.fsync', side_effect=fail_directory_sync):
                with self.assertRaisesRegex(OSError, 'injected directory fsync failure'):
                    publish(slot, expected)

            self.assertEqual(calls, 2, 'fail only after the file fsync and exclusive link')
            self.assertEqual(slot.read_bytes(), expected)
            self.assertEqual(sorted(path.name for path in Path(directory).iterdir()), ['request.json'])
            with self.assertRaises(FileExistsError):
                publish(slot, b'{"id":1,"tool":"replay"}\n')
            self.assertEqual(slot.read_bytes(), expected)
            self.assertEqual(sorted(path.name for path in Path(directory).iterdir()), ['request.json'])


if __name__ == '__main__':
    unittest.main()
