import json
import os
import time
import unittest
import focus_pipe
import app
from focus_trace import FocusTrace


class PublisherTests(unittest.TestCase):
    def test_app_focus_callback_joins_memory_event_to_actual_pipe_frame(self):
        self.assertTrue(hasattr(app,'record_focus'))
        read_fd,write_fd=os.pipe()
        publisher=focus_pipe.FocusPipe(write_fd,{'token':'fresh','pid':os.getpid(),
            'target_id':42,'freeze_sha256':'a'*64})
        trace=FocusTrace('MEMORY_ONLY')
        try:
            event=app.record_focus(trace,publisher,'FocusOut','target',publisher.binding,'other')
            os.set_blocking(read_fd,False)
            value=json.loads(os.read(read_fd,512))
            self.assertEqual(value['kind'],'FocusOut')
            self.assertEqual(value['event_ns'],event['monotonic_ns'])
            self.assertEqual(value['sequence'],event['sequence'])
            self.assertEqual(trace.snapshot()['publications'],[])
        finally:publisher.close();os.close(read_fd)

    def test_actual_event_bytes_preserve_binding_and_sequence(self):
        self.assertTrue(hasattr(focus_pipe,'FocusPipe'))
        read_fd,write_fd=os.pipe()
        try:
            publisher=focus_pipe.FocusPipe(write_fd,{'token':'fresh','pid':os.getpid(),
                'target_id':42,'freeze_sha256':'a'*64})
            event={'kind':'FocusIn','widget':'target','sequence':3,'monotonic_ns':time.monotonic_ns()}
            publisher.publish(event,'target')
            os.set_blocking(read_fd,False)
            value=json.loads(os.read(read_fd,512))
            self.assertEqual(value['schema'],'issue5260-a09-focus-pipe-v1')
            self.assertEqual(value['sequence'],3)
            self.assertEqual(value['event_ns'],event['monotonic_ns'])
            self.assertEqual(value['freeze_sha256'],'a'*64)
            self.assertEqual(publisher.snapshot()['first_error'],None)
            publisher.close()
            self.assertEqual(os.read(read_fd,512),b'')
            self.assertIsNone(publisher.fd)
        finally:
            os.close(read_fd)
            if 'publisher' in locals():publisher.close()
            else:os.close(write_fd)

    def test_actual_broken_pipe_is_retained_and_never_retried(self):
        self.assertTrue(hasattr(focus_pipe,'FocusPipe'))
        read_fd,write_fd=os.pipe()
        publisher=focus_pipe.FocusPipe(write_fd,{'token':'fresh','pid':os.getpid(),
            'target_id':42,'freeze_sha256':'a'*64})
        os.close(read_fd)
        try:
            event={'kind':'FocusIn','widget':'target','sequence':1,'monotonic_ns':time.monotonic_ns()}
            self.assertFalse(publisher.publish(event,'target'))
            first=publisher.snapshot()['first_error']
            self.assertIsNotNone(first)
            self.assertFalse(publisher.publish({**event,'sequence':2},'target'))
            self.assertEqual(len(publisher.snapshot()['publications']),1)
            self.assertEqual(publisher.snapshot()['first_error'],first)
        finally:publisher.close()


if __name__=='__main__':unittest.main()
