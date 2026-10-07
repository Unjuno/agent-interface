import copy
import json
import socket
import socketserver
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from release_event_socket_v1 import ReleaseEventSocket
from release_pending_action_v1 import PendingAction


def exchange(path, request):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.connect(str(path)); client.sendall((json.dumps(request) + "\n").encode())
        with client.makefile("rb") as stream: return json.loads(stream.readline())


class ReleaseDeliveryTests(unittest.TestCase):
    def rows(self):
        accepted = {"event": "accepted", "id": "p", "intent_token": "t"}
        release = {"event": "input_released", "id": "p", "intent_token": "t",
            "owner_release": {"verified": True, "keys_down": [], "buttons_down": []},
            "program_terminal_pending": True, "grants_input_authority": False}
        terminal = {"event": "terminal", "id": "p", "status": "needs_decision",
            "interruption": {"intent_token": "t", "record": release["owner_release"]}}
        return accepted, release, terminal

    @unittest.skipUnless(hasattr(socketserver, "UnixStreamServer"), "Unix socket server required")
    def test_socket_returns_release_before_later_terminal(self):
        server = ReleaseEventSocket()
        try:
            for row in self.rows()[:2]: server.append(row)
            reply = exchange(server.path, {"after": 0,
                "events": ["input_released", "terminal"], "timeout": 1,
                "action_id": "p", "request_id": "early"})
            self.assertEqual(reply["records"][-1]["event"], "input_released")
            state = PendingAction("p").ingest(reply)
            self.assertEqual(state["state"], "input_released_terminal_pending")
            self.assertTrue(state["physical_release_verified"])
        finally: server.close()

    def test_wrong_token_or_conflicting_terminal_fails_closed(self):
        accepted, release, terminal = self.rows()
        for mutate in (lambda r: r[1].update(intent_token="wrong"),
                       lambda r: r[1]["owner_release"].update(verified=False),
                       lambda r: r[2]["interruption"].update(intent_token="wrong")):
            rows = copy.deepcopy([accepted, release, terminal]); mutate(rows)
            tracker = PendingAction("p")
            view = tracker.ingest({"status": "boundary", "records": rows})
            self.assertEqual(view["state"], "needs_reconciliation")


if __name__ == "__main__": unittest.main()
