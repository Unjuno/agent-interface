import io,os,sys,tempfile,threading,unittest
from pathlib import Path
from job_host import JobHost, _Reader
from unittest.mock import patch

@unittest.skipUnless(sys.platform=='win32','Windows only')
class JobHostTests(unittest.TestCase):
    def test_reader_preserves_short_file_writes(self):
        class ShortWriter:
            def __init__(self):self.data=bytearray();self.closed=False
            def write(self, data):
                n=min(2,len(data));self.data.extend(data[:n]);return n
            def close(self):self.closed=True
        writer=ShortWriter();reader=_Reader('test',io.BytesIO(b'abcdef'),writer,threading.Event())
        reader.start();reader.thread.join(2)
        self.assertTrue(reader.eof);self.assertEqual(reader.errors,[])
        self.assertEqual(bytes(writer.data),b'abcdef');self.assertEqual(reader.bytes,6)

    def test_non_bytes_read_is_not_eof(self):
        class Indeterminate:
            def __init__(self,value):self.value=value
            def read(self, size):return self.value
        class Sink:
            def close(self):pass
        for value in (None,bytearray(),memoryview(b'')):
            with self.subTest(value=type(value).__name__):
                failed=threading.Event();reader=_Reader('test',Indeterminate(value),Sink(),failed)
                reader.start();reader.thread.join(2)
                self.assertTrue(failed.is_set());self.assertFalse(reader.eof)
                self.assertEqual(reader.errors,['OSError'])

    def test_reader_exception_is_not_eof(self):
        class Broken:
            def read(self, size):raise OSError('injected')
        class Sink:
            def close(self):pass
        failed=threading.Event();reader=_Reader('test',Broken(),Sink(),failed)
        reader.start();reader.thread.join(2)
        self.assertTrue(failed.is_set());self.assertFalse(reader.eof)
        self.assertEqual(reader.errors,['OSError'])

    def test_late_exit_and_late_close_are_not_timely_success(self):
        now={'t':0,'late':True}
        class Process:
            def wait(self,timeout):now['t']=2;return 0
            def close(self,timeout_s):
                if now['late']:now['t']=2
                return {'job_closed':True,'process_exited':True,'kernel_handles_closed':True,'errors':[]}
            def close_streams(self):return {'streams_closed':True,'errors':[]}
        class Sink:
            def write(self,data):return len(data)
            def close(self):pass
        def make_host(d):
            host=JobHost([sys.executable],d);host.process=Process();host.start_complete=True
            host.readers={name:_Reader(name,io.BytesIO(b'data'),Sink(),host.failure) for name in ('stdout','stderr')}
            for reader in host.readers.values():reader.start();reader.thread.join(2)
            return host
        with tempfile.TemporaryDirectory() as d, patch('job_host.time.monotonic',side_effect=lambda:now['t']):
            host=make_host(d);result=host.wait(timeout_s=1)
            self.assertEqual(result['status'],'UNKNOWN');self.assertEqual(result['observed_exit_code'],0)
            now['t']=0;result=host.close(timeout_s=1)
            self.assertEqual(result['status'],'UNKNOWN');self.assertTrue(result['deadline_exceeded'])
            self.assertTrue(all(x['eof'] and not x['errors'] for x in result['readers'].values()))
            now['t']=0;now['late']=False;control=make_host(d).close(timeout_s=1)
            self.assertEqual(control['status'],'closed_scoped')
            self.assertFalse(control['deadline_exceeded'])

    def test_concurrent_large_stdout_stderr_are_drained(self):
        code="import os,threading; f=lambda fd,c:[os.write(fd,c*4096) for _ in range(128)]; a=threading.Thread(target=f,args=(1,b'A'));b=threading.Thread(target=f,args=(2,b'B'));a.start();b.start();a.join();b.join()"
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);host=JobHost([sys.executable,'-u','-c',code],root,cwd=d,environment=dict(os.environ))
            try:
                host.start();wait=host.wait(timeout_s=10);self.assertEqual(wait['exit_code'],0)
                result=host.close(timeout_s=5)
                self.assertEqual(result['status'],'closed_scoped')
                self.assertEqual((root/'stdout.bin').stat().st_size,4096*128)
                self.assertEqual((root/'stderr.bin').stat().st_size,4096*128)
                self.assertEqual((root/'stdout.bin').read_bytes(),b'A'*(4096*128))
                self.assertEqual((root/'stderr.bin').read_bytes(),b'B'*(4096*128))
                self.assertTrue(result['readers']['stdout']['eof'])
                self.assertTrue(result['readers']['stderr']['eof'])
            finally:host.close(timeout_s=5)

    def test_reader_write_failure_is_reported(self):
        class Sink:
            def write(self, data):raise OSError('disk')
            def close(self):pass
        failed=threading.Event();reader=_Reader('test',io.BytesIO(b'data'),Sink(),failed)
        reader.start();reader.thread.join(2)
        self.assertTrue(failed.is_set());self.assertFalse(reader.eof)
        self.assertEqual(reader.errors,['OSError'])
        with tempfile.TemporaryDirectory() as d:
            host=JobHost([sys.executable],d);host.start_complete=True;host.failure.set()
            self.assertEqual(host.wait(timeout_s=1)['reason'],'reader_error')

    def test_second_reader_start_failure_retires_known_process(self):
        with tempfile.TemporaryDirectory() as d:
            host=JobHost([sys.executable,'-c','import time;time.sleep(30)'],d)
            original=_Reader.start;calls=[]
            def fail_second(reader):
                calls.append(1)
                if len(calls)==2:raise RuntimeError('injected before thread start')
                return original(reader)
            try:
                with patch.object(_Reader,'start',fail_second):
                    with self.assertRaises(RuntimeError):host.start()
                receipt=host.close(timeout_s=5)
                self.assertTrue(receipt['process']['job_closed'])
                self.assertTrue(receipt['process']['process_exited'])
                self.assertEqual(receipt['status'],'UNKNOWN')
            finally:host.close(timeout_s=5)

    def test_second_thread_start_prelaunch_failure_closes_only_unstarted_log(self):
        with tempfile.TemporaryDirectory() as d:
            host=JobHost([sys.executable,'-c','import time;time.sleep(30)'],d)
            original=threading.Thread.start;calls=[]
            def fail_second(thread):
                calls.append(thread)
                if len(calls)==2:raise RuntimeError('injected before OS thread creation')
                return original(thread)
            try:
                with patch.object(threading.Thread,'start',fail_second):
                    with self.assertRaises(RuntimeError):host.start()
                receipt=host.close(timeout_s=5)
                self.assertEqual(receipt['readers']['stderr']['start_state'],'not_started')
                self.assertTrue(receipt['streams']['streams_closed'])
                self.assertTrue(host.readers['stderr'].output.closed)
                self.assertEqual(receipt['status'],'UNKNOWN')
            finally:host.close(timeout_s=5)

    def test_second_thread_start_ambiguous_failure_keeps_unknown(self):
        with tempfile.TemporaryDirectory() as d:
            host=JobHost([sys.executable,'-c','import time;time.sleep(30)'],d)
            original=threading.Thread.start;calls=[]
            def start_then_raise(thread):
                calls.append(thread)
                original(thread)
                if len(calls)==2:raise RuntimeError('injected after OS thread creation')
            try:
                with patch.object(threading.Thread,'start',start_then_raise):
                    with self.assertRaises(RuntimeError):host.start()
                receipt=host.close(timeout_s=5)
                self.assertEqual(receipt['readers']['stderr']['start_state'],'unknown')
                self.assertFalse(receipt['readers']['stderr']['started'])
                self.assertTrue(receipt['streams']['streams_closed'])
                self.assertEqual(receipt['status'],'UNKNOWN')
            finally:host.close(timeout_s=5)

    def test_partial_output_followed_by_timeout_is_not_success(self):
        code="import sys,time;sys.stdout.write('{partial');sys.stdout.flush();time.sleep(30)"
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);host=JobHost([sys.executable,'-u','-c',code],root)
            try:
                host.start();wait=host.wait(timeout_s=.5);self.assertEqual(wait['status'],'UNKNOWN')
                receipt=host.close(timeout_s=5)
                self.assertEqual(receipt['status'],'closed_scoped')
                self.assertEqual((root/'stdout.bin').read_bytes(),b'{partial')
                self.assertNotIn('exit_code',wait)
            finally:host.close(timeout_s=5)

    def test_exited_host_with_inherited_stdout_is_drained_after_job_close(self):
        child="import time;print('grandchild',flush=True);time.sleep(30)"
        code="import subprocess,sys,time;subprocess.Popen([sys.executable,'-u','-c',%r],close_fds=False);time.sleep(.5)"%child
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);host=JobHost([sys.executable,'-u','-c',code],root)
            try:
                host.start();self.assertEqual(host.wait(timeout_s=8)['exit_code'],0)
                self.assertFalse(host.readers['stdout'].done.is_set())
                result=host.close(timeout_s=5);self.assertEqual(result['status'],'closed_scoped')
                self.assertIn(b'grandchild',(root/'stdout.bin').read_bytes())
            finally:host.close(timeout_s=5)

if __name__=='__main__':unittest.main()
