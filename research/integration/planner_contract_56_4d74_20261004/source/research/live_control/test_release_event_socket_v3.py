import sys
import socketserver
import threading
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from release_event_socket_v3 import ReleaseEventSocket
from unix_json_deadline import exchange


class ReleaseEventSocketV3Tests(unittest.TestCase):
    @unittest.skipUnless(hasattr(socketserver, "UnixStreamServer"),
                         "Unix domain socket server required")
    def test_registered_client_receives_only_matching_semantic_boundary(self):
        delivery = ReleaseEventSocket()
        result = {}
        request = {"after": 0, "events": ["semantic_probe", "terminal"],
                   "timeout": 1, "action_id": "target", "request_id": "probe-0"}
        thread = threading.Thread(target=lambda: result.update(
            reply=exchange(delivery.path, request, timeout=2)))
        try:
            thread.start()
            self.assertTrue(delivery.wait_requests(1))
            delivery.append({"event": "semantic_probe", "id": "other",
                             "score": {"success": True}})
            delivery.append({"event": "semantic_probe", "id": "target",
                             "score": {"success": False},
                             "grants_input_authority": False})
            thread.join(2)
            self.assertFalse(thread.is_alive())
            self.assertEqual(result["reply"]["records"][-1]["id"], "target")
            self.assertEqual(result["reply"]["authority"], "none")
            self.assertEqual(delivery.request_receipts()[0]["request_id"], "probe-0")
        finally:
            delivery.close()


if __name__ == "__main__":
    unittest.main()
