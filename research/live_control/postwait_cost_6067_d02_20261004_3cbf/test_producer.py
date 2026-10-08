"""Real owned-child IPC and cleanup; no X server/GUI/native allocation."""
import os
import subprocess
import sys
import unittest
from producer import read_display,terminal

class ProducerTests(unittest.TestCase):
    def test_child_owned_display_descriptor(self):
        r,w=os.pipe()
        p=subprocess.Popen([sys.executable,'-c',
            'import os,sys,time;os.write(int(sys.argv[1]),b"4\\n");time.sleep(2)',str(w)],pass_fds=(w,))
        os.close(w)
        try: self.assertEqual(read_display(p,r,.5),':4')
        finally: os.close(r); terminal(p)

    def test_dead_server_does_not_gain_ownership(self):
        r,w=os.pipe()
        p=subprocess.Popen([sys.executable,'-c','pass'],pass_fds=(w,)); os.close(w); p.wait()
        try:
            with self.assertRaises(RuntimeError): read_display(p,r,.1)
        finally: os.close(r)

    def test_display_descriptor_timeout_is_bounded(self):
        r,w=os.pipe()
        p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(2)'],pass_fds=(w,)); os.close(w)
        try:
            with self.assertRaises(RuntimeError): read_display(p,r,.02)
        finally: os.close(r); terminal(p)

    def test_intentional_sigterm_has_real_terminal_receipt(self):
        p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(2)'])
        self.assertEqual(terminal(p),-15)

if __name__=='__main__': unittest.main()
