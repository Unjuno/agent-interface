import os
import subprocess
import sys
import unittest
import pipe_transport


class TransportTests(unittest.TestCase):
    @unittest.skipUnless(os.name=='posix','pass_fds requires Linux/POSIX')
    def test_child_inherits_only_writer_and_stdout_stays_separate(self):
        with pipe_transport.PipeSession() as session:
            self.assertGreaterEqual(session.identity['pipe_buf'],512)
            child=subprocess.Popen([sys.executable,'-c',
                'import os,sys; os.write(int(sys.argv[1]),b\'{"x":1}\\n\'); print("RESULT",flush=True)',
                str(session.write_fd)],pass_fds=(session.write_fd,),
                stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            session.release_parent_writer()
            stdout,stderr=child.communicate(timeout=3)
            self.assertEqual(child.returncode,0)
            self.assertEqual(stdout,'RESULT\n')
            self.assertEqual(stderr,'')
            self.assertEqual(session.drain(),[{'x':1}])
            self.assertTrue(session.eof)

    def test_empty_live_pipe_records_eagain_without_waiting(self):
        self.assertTrue(hasattr(pipe_transport, 'PipeSession'))
        with pipe_transport.PipeSession() as session:
            self.assertEqual(session.drain(), [])
            self.assertEqual(session.reads[-1]['status'], 'EAGAIN')
            self.assertFalse(session.eof)

    def test_real_frames_and_eof_retain_exact_read_bytes(self):
        self.assertTrue(hasattr(pipe_transport, 'PipeSession'))
        with pipe_transport.PipeSession() as session:
            os.write(session.write_fd, b'{"x":1}\n{"x":2}\n')
            session.release_parent_writer()
            self.assertEqual(session.drain(), [{'x':1}, {'x':2}])
            self.assertTrue(session.eof)
            self.assertEqual(bytes.fromhex(session.reads[0]['hex']), b'{"x":1}\n{"x":2}\n')
            self.assertEqual(session.reads[-1]['status'], 'EOF')
            self.assertIsNone(session.finish())

    def test_partial_frame_at_actual_eof_is_refused(self):
        self.assertTrue(hasattr(pipe_transport, 'PipeSession'))
        with pipe_transport.PipeSession() as session:
            os.write(session.write_fd, b'{"x":')
            session.release_parent_writer()
            with self.assertRaises(ValueError): session.drain()

    def test_closing_session_cannot_close_a_reused_writer_descriptor(self):
        self.assertTrue(hasattr(pipe_transport, 'PipeSession'))
        session=pipe_transport.PipeSession()
        session.release_parent_writer()
        other_read, other_write=os.pipe()
        try:
            session.close()
            os.write(other_write, b'x')
            self.assertEqual(os.read(other_read, 1), b'x')
            self.assertIsNone(session.read_fd)
            self.assertIsNone(session.write_fd)
        finally:
            session.close()
            os.close(other_read)
            os.close(other_write)


if __name__=='__main__': unittest.main()
