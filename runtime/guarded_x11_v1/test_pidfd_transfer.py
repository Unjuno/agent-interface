import array,os,socket,subprocess,sys,unittest
from unittest import mock



def count():
    n=0
    for path in os.listdir('/proc/self/fd'):
        try:n+=os.readlink('/proc/self/fd/'+path)=='anon_inode:[pidfd]'
        except FileNotFoundError:pass
    return n

@unittest.skipUnless(sys.platform.startswith('linux') and hasattr(os, 'pidfd_open') and hasattr(socket, 'SCM_RIGHTS') and hasattr(socket, 'MSG_CMSG_CLOEXEC'), 'Linux pidfd and SCM_RIGHTS required')
class TransferTests(unittest.TestCase):
    def setUp(self):
        global send_pidfd, receive_pidfd, TransferError
        from runtime.guarded_x11_v1.pidfd_transfer import send_pidfd, receive_pidfd, TransferError
        self.proc=subprocess.Popen([sys.executable,'-c','import time;time.sleep(20)']);self.fd=os.pidfd_open(self.proc.pid)
        self.a,self.b=socket.socketpair();self.a.setblocking(False);self.b.setblocking(False);self.baseline=count()
    def tearDown(self):
        self.a.close();self.b.close();os.close(self.fd);self.proc.terminate();self.proc.wait(timeout=3)
    def test_success(self):
        send_pidfd(self.a,self.fd);received=receive_pidfd(self.b)
        try:self.assertFalse(os.get_inheritable(received));self.assertEqual(count(),self.baseline+1)
        finally:os.close(received)
        self.assertEqual(count(),self.baseline)
    def test_missing_fd_rejected(self):
        self.a.send(b'P')
        with self.assertRaises(TransferError):receive_pidfd(self.b)
        self.assertEqual(count(),self.baseline)
    def test_wrong_marker_closes_received(self):
        self.a.sendmsg([b'X'],[(socket.SOL_SOCKET,socket.SCM_RIGHTS,array.array('i',[self.fd]))])
        with self.assertRaises(TransferError):receive_pidfd(self.b)
        self.assertEqual(count(),self.baseline)
    def test_multiple_fds_closed(self):
        self.a.sendmsg([b'P'],[(socket.SOL_SOCKET,socket.SCM_RIGHTS,array.array('i',[self.fd,self.fd]))])
        with self.assertRaises(TransferError):receive_pidfd(self.b)
        self.assertEqual(count(),self.baseline)
    def test_truncated_rights_closed(self):
        self.a.sendmsg([b'P'],[(socket.SOL_SOCKET,socket.SCM_RIGHTS,array.array('i',[self.fd]*16))])
        with self.assertRaises(TransferError):receive_pidfd(self.b)
        self.assertEqual(count(),self.baseline)
    def test_blocking_socket_rejected(self):
        self.a.setblocking(True)
        with self.assertRaises(ValueError):send_pidfd(self.a,self.fd)
        self.b.setblocking(True)
        with self.assertRaises(ValueError):receive_pidfd(self.b)
        self.assertEqual(count(),self.baseline)
    def test_eof_rejected(self):
        self.a.close()
        with self.assertRaises(TransferError):receive_pidfd(self.b)
        self.assertEqual(count(),self.baseline)
    def test_empty_socket_would_block(self):
        with self.assertRaises(BlockingIOError):receive_pidfd(self.b)
        self.assertEqual(count(),self.baseline)
    def test_backpressure_no_late_fd(self):
        self.a.setsockopt(socket.SOL_SOCKET,socket.SO_SNDBUF,4096)
        while True:
            try:self.a.send(b'x'*4096)
            except BlockingIOError:break
        with self.assertRaises(BlockingIOError):send_pidfd(self.a,self.fd)
        while True:
            try:
                payload,anc,flags,addr=self.b.recvmsg(65536,socket.CMSG_SPACE(4*4))
                self.assertFalse(anc)
            except BlockingIOError:break
        self.assertEqual(count(),self.baseline)
    def test_seqpacket_rejected_before_send_and_receive(self):
        a, b = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
        self.addCleanup(a.close)
        self.addCleanup(b.close)
        a.setblocking(False)
        b.setblocking(False)
        with self.assertRaises(ValueError): send_pidfd(a, self.fd)
        with self.assertRaises(ValueError): receive_pidfd(b)

    def test_passpidfd_rejection_closes_all_received_descriptors(self):
        try:
            self.b.setsockopt(socket.SOL_SOCKET, 76, 1)  # Linux SO_PASSPIDFD
        except OSError as error:
            self.skipTest('SO_PASSPIDFD unavailable: ' + str(error))
        send_pidfd(self.a, self.fd)
        with self.assertRaises(TransferError): receive_pidfd(self.b)
        self.assertEqual(count(), self.baseline)

    def test_close_error_still_attempts_other_received_descriptors(self):
        self.a.sendmsg([b'P'], [(socket.SOL_SOCKET, socket.SCM_RIGHTS,
                               array.array('i', [self.fd, self.fd]))])
        original = os.close
        closed = []
        def close_then_first_error(fd):
            closed.append(fd)
            original(fd)
            if len(closed) == 1:
                raise OSError('injected uncertain close')
        with mock.patch('runtime.guarded_x11_v1.pidfd_transfer.os.close',
                        side_effect=close_then_first_error):
            with self.assertRaisesRegex(OSError, 'injected uncertain close'):
                receive_pidfd(self.b)
        self.assertEqual(len(closed), 2)
        self.assertEqual(count(), self.baseline)

if __name__=='__main__':unittest.main(verbosity=2)
