import sys
import threading
import time
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from release_event_cursor_v2 import EventCursor


class ReleaseEventCursorV2Tests(unittest.TestCase):
    def test_semantic_probe_is_action_scoped(self):
        cursor = EventCursor()
        cursor.append({"event": "semantic_probe", "id": "other", "score": {"success": True}})
        cursor.append({"event": "semantic_probe", "id": "target", "score": {"success": False}})
        result = cursor.read_until(0, ["semantic_probe", "terminal"], 0, "target")
        self.assertEqual(result["status"], "boundary")
        self.assertEqual(result["records"][-1]["id"], "target")
        self.assertEqual(result["authority"], "none")

    def test_semantic_wait_can_resolve_terminal(self):
        cursor = EventCursor()
        def publish():
            time.sleep(.01)
            cursor.append({"event": "terminal", "id": "target", "status": "completed"})
        thread = threading.Thread(target=publish); thread.start()
        result = cursor.read_until(0, ["semantic_probe", "terminal"], 1, "target")
        thread.join()
        self.assertEqual(result["records"][-1]["event"], "terminal")

    def test_unscoped_unknown_event_remains_allowed(self):
        cursor = EventCursor()
        cursor.append({"event": "diagnostic"})
        self.assertEqual(cursor.read_until(0, ["diagnostic"], 0)["status"], "boundary")

    def test_scoped_unknown_event_is_rejected(self):
        cursor = EventCursor()
        with self.assertRaises(ValueError):
            cursor.read_until(0, ["diagnostic"], 0, "target")


if __name__ == "__main__":
    unittest.main()
