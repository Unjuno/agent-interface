"""Compose V39 retirement with the real adapter/client and an owned fake pipe."""
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "live_control"), str(HERE.parents[1])]
import map01_overlap_controller_v39 as controller
import codex_app_server_client_v2 as client_module
from research.live_control import test_codex_app_server_send_deadline_v1 as fixture

class RetirementCompositionTests(unittest.TestCase):
    def test_real_client_fence_timeout_then_controller_retry_wakes_waiter(self):
        with patch.object(fixture, "module", client_module), fixture.owned_client() as (client, _read_fd):
            waiting, held, release = (threading.Event() for _ in range(3))
            events = []
            original_wait, original_close = client._condition.wait, client.close
            planner = controller.PersistentPlannerAdapter(client, model="fixture", effort="low", cwd=".", base_instructions="")
            def wait_marker(timeout=None):
                waiting.set()
                return original_wait(timeout)
            def bounded_close(timeout=5):
                events.append("close_attempt")
                try:
                    return original_close(timeout=.05)
                except client_module.AppServerConditionFenceTimeout:
                    events.append("fence_timeout")
                    release.set()
                    blocker.join(1)
                    raise
            with patch.object(client, "start_thread", return_value={"thread":{"id":"fixture-thread"}}), \
                 patch.object(client, "start_turn", return_value={"turn":{"id":"fixture-turn"}}), \
                 patch.object(client, "close", side_effect=bounded_close), tempfile.TemporaryDirectory() as root:
                planner.start_session()
                handle = planner.begin_turn("observe", output_schema={"type":"object"})
                client._condition.wait = wait_marker
                def holder():
                    with client._condition:
                        held.set()
                        release.wait(2)
                blocker = threading.Thread(target=holder)
                with ThreadPoolExecutor(max_workers=1) as pool:
                    future = pool.submit(planner.await_turn, handle, 2)
                    try:
                        self.assertTrue(waiting.wait(1))
                        blocker.start()
                        self.assertTrue(held.wait(1))
                        terminal = {"event":"terminal", "status":"completed", "id":"cover-0",
                                    "release":{"event":"owner_release", "verified":True,
                                               "keys_down":[], "buttons_down":[],
                                               "keys_unknown":[], "key_state_errors":[]}}
                        error = RuntimeError("renewal rejected")
                        controller.retire_failed_cover(planner, handle, future, terminal, error, root)
                        with self.assertRaises(client_module.AppServerError):
                            future.result(timeout=1)
                        self.assertEqual(events, ["close_attempt", "fence_timeout", "close_attempt"])
                        self.assertTrue(planner._cancellation_requested)
                        self.assertIn("pending planner turn transport aborted", error.__notes__)
                        receipt = json.loads((Path(root)/"fatal-cover-terminal.json").read_text())
                        self.assertFalse(receipt["grants_input_authority"])
                        self.assertEqual(receipt["terminal"], terminal)
                    finally:
                        release.set()
                        if blocker.ident is not None: blocker.join(1)
                        client._condition.wait = original_wait

if __name__ == "__main__": unittest.main()
