from pathlib import Path
import tempfile
import unittest
from candidate import planned_rows, read_payload


class ReaderTests(unittest.TestCase):
    def test_schedule_has_eight_unique_cells(self):
        rows=planned_rows({'seed':52606026})
        self.assertEqual(len(rows),8)
        self.assertEqual(len({tuple(sorted(r.items())) for r in rows}),8)

    def test_first_success_keeps_exact_bytes_and_poll_clocks(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'receipt.json';path.write_bytes(b'{"token":"fresh"}\n')
            payload,blob,attempts=read_payload(path,100)
            self.assertEqual(payload,{'token':'fresh'})
            self.assertEqual(blob,b'{"token":"fresh"}\n')
            self.assertEqual(len(attempts),1)
            self.assertEqual(attempts[0]['status'],'READ_OK')
            self.assertLessEqual(attempts[0]['start_ns'],attempts[0]['end_ns'])

    def test_absent_file_stops_without_a_writer_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(TimeoutError):
                read_payload(Path(directory)/'absent',2)


if __name__=='__main__':unittest.main()
