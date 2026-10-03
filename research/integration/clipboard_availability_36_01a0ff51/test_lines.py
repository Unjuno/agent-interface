import json
import subprocess
import sys
import time
import unittest
from run import Lines


class Framing(unittest.TestCase):
    def test_partial_line_obeys_deadline(self):
        p = subprocess.Popen([sys.executable, '-c', "import sys,time;sys.stdout.write('{');sys.stdout.flush();time.sleep(2)"], stdout=subprocess.PIPE)
        try:
            start = time.monotonic()
            with self.assertRaises(TimeoutError): Lines(p).read(.1)
            self.assertLess(time.monotonic() - start, 1)
        finally: p.kill(); p.wait(timeout=1); p.stdout.close()

    def test_buffered_messages_keep_association(self):
        p = subprocess.Popen([sys.executable, '-c', "print('{\"op\":\"first\"}');print('{\"op\":\"second\"}')"], stdout=subprocess.PIPE)
        try:
            reader = Lines(p)
            self.assertEqual(reader.read(1), {'op': 'first'})
            self.assertEqual(reader.read(1), {'op': 'second'})
        finally: p.wait(timeout=1); p.stdout.close()


if __name__ == '__main__': unittest.main()
