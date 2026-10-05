import os,time,unittest
from doom_controller_failure_cleanup_v1 import send_failure_finish

class Tests(unittest.TestCase):
    def test_full_pipe_times_out_without_blocking(self):
        read_fd,write_fd=os.pipe()
        try:
            os.set_blocking(write_fd,False)
            while True:
                try: os.write(write_fd,b'x'*4096)
                except BlockingIOError: break
            os.set_blocking(write_fd,True)
            with os.fdopen(write_fd,'w',closefd=False) as stream:
                started=time.monotonic()
                with self.assertRaises(TimeoutError): send_failure_finish(stream,timeout=.05)
                self.assertLess(time.monotonic()-started,1)
                self.assertTrue(os.get_blocking(write_fd))
        finally: os.close(read_fd);os.close(write_fd)
    def test_readable_pipe_gets_exact_finish_and_mode_restored(self):
        read_fd,write_fd=os.pipe()
        try:
            with os.fdopen(write_fd,'w',closefd=False) as stream:
                send_failure_finish(stream,timeout=.05)
                self.assertEqual(os.read(read_fd,100),b'{"op":"finish"}\n')
                self.assertTrue(os.get_blocking(write_fd))
        finally: os.close(read_fd);os.close(write_fd)

if __name__=='__main__': unittest.main()
