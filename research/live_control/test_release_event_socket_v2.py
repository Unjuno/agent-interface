import socketserver
import sys
import threading
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
from release_event_socket_v2 import ReleaseEventSocket
from test_release_delivery_v1 import exchange


@unittest.skipUnless(hasattr(socketserver, "UnixStreamServer"), "Unix socket server required")
class ReleaseEventSocketV2Tests(unittest.TestCase):
    def test_request_receipts_are_copied_before_boundary(self):
        server = ReleaseEventSocket(); reply = {}
        try:
            request = {"after": 0, "events": ["terminal"], "timeout": 1,
                       "action_id": "p", "request_id": "terminal-only"}
            thread = threading.Thread(target=lambda: reply.update(exchange(server.path, request)))
            thread.start(); self.assertTrue(server.wait_requests(1))
            receipts = server.request_receipts()
            self.assertEqual(receipts[0]["request"], request)
            receipts[0]["request"]["events"] = ["input_released"]
            self.assertEqual(server.request_receipts()[0]["request"]["events"], ["terminal"])
            server.append({"event": "terminal", "id": "p"}); thread.join()
            self.assertEqual(reply["status"], "boundary")
        finally: server.close()

if __name__ == "__main__": unittest.main()
