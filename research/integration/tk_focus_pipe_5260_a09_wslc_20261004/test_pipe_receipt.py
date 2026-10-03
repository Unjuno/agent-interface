import copy
import os
import unittest
from pipe_receipt import encode_frame,FrameDecoder,admission_errors,write_once,PipeWriteError


class FrameTests(unittest.TestCase):
    def test_exact_one_line_utf8_frame(self):
        self.assertEqual(encode_frame({'x':1}),b'{"x":1}\n')

    def test_oversized_frame_is_rejected_before_transport(self):
        with self.assertRaises(ValueError):encode_frame({'x':'z'*512})

    def test_partial_and_two_frames_are_decoded_in_order(self):
        decoder=FrameDecoder()
        self.assertEqual(decoder.feed(b'{"x":'),[])
        self.assertEqual(decoder.feed(b'1}\n{"x":2}\n'),[{'x':1},{'x':2}])
        self.assertIsNone(decoder.finish())

    def test_bad_json_partial_eof_and_total_budget_rejected(self):
        with self.assertRaises(ValueError):FrameDecoder().feed(b'{bad}\n')
        decoder=FrameDecoder();decoder.feed(b'{"x":1')
        with self.assertRaises(ValueError):decoder.finish()
        with self.assertRaises(ValueError):FrameDecoder(max_total_bytes=4).feed(b'{"x":1}\n')

    def test_duplicate_keys_nan_and_nonobject_frames_refused(self):
        for blob in (b'{"pid":17,"pid":18}\n',b'{"x":NaN}\n',b'[]\n',b'{"x":"\xff"}\n'):
            with self.assertRaises(ValueError):FrameDecoder().feed(blob)

    def test_decoder_does_not_resume_after_transport_error(self):
        decoder=FrameDecoder()
        with self.assertRaises(ValueError):decoder.feed(b'{bad}\n')
        with self.assertRaises(ValueError):decoder.feed(b'{"x":1}\n')

    def test_frame_stream_is_closed_after_complete_eof(self):
        decoder=FrameDecoder();decoder.feed(b'{"x":1}\n');decoder.finish()
        with self.assertRaises(ValueError):decoder.feed(b'{"x":2}\n')

    def test_real_pipe_transmits_exact_frame(self):
        read_fd,write_fd=os.pipe()
        try:
            trace=write_once(write_fd,{'x':1})
            os.set_blocking(read_fd,False)
            try:actual=os.read(read_fd,512)
            except BlockingIOError:actual=b''
            self.assertEqual(actual,b'{"x":1}\n')
            self.assertEqual(trace['written_bytes'],8)
            self.assertGreaterEqual(trace['completed_ns'],trace['started_ns'])
        finally:os.close(read_fd);os.close(write_fd)

    def test_real_short_write_fails_without_retry(self):
        read_fd,write_fd=os.pipe()
        try:
            with self.assertRaises(PipeWriteError) as result:
                write_once(write_fd,{'x':1},write=lambda fd,data:os.write(fd,data[:1]))
            os.set_blocking(read_fd,False)
            self.assertEqual(os.read(read_fd,512),b'{')
            self.assertEqual(result.exception.trace['written_bytes'],1)
            self.assertEqual(result.exception.trace['requested_bytes'],8)
        finally:os.close(read_fd);os.close(write_fd)


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.binding={'token':'fresh','pid':17,'target_id':42,'freeze_sha256':'a'*64}
        self.receipt={**self.binding,'schema':'issue5260-a09-focus-pipe-v1',
            'kind':'FocusIn','widget':'target','focus_get':'target','sequence':3,
            'event_ns':200,'written_ns':201}

    def test_fresh_target_receipt_admits(self):
        self.assertEqual(admission_errors(self.receipt,self.binding,300,100),[])

    def test_wrong_pid_token_target_source_and_focus_refused(self):
        for field,value in (('pid',18),('token','other'),('target_id',43),
                            ('freeze_sha256','b'*64),('kind','FocusOut'),
                            ('widget','decoy'),('focus_get','other')):
            receipt=copy.deepcopy(self.receipt);receipt[field]=value
            self.assertTrue(admission_errors(receipt,self.binding,300,100),field)

    def test_boolean_stale_future_preclick_and_bad_sequence_refused(self):
        for field,value in (('pid',True),('target_id',True),('sequence',True),
                            ('event_ns',True),('written_ns',True),('sequence',0),
                            ('event_ns',99),('written_ns',400)):
            receipt=copy.deepcopy(self.receipt);receipt[field]=value
            self.assertTrue(admission_errors(receipt,self.binding,300,100),field)
        self.assertTrue(admission_errors(self.receipt,self.binding,50_000_202,100))


if __name__=='__main__':unittest.main()
