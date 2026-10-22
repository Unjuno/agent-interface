"""Local-only checks for the Chromium task fixture; no browser/model is started."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.parse import urlencode
from urllib.request import Request, urlopen


RUNNER = Path(__file__).with_name("run_public_caller_r01.py")
SPEC = importlib.util.spec_from_file_location("chromium_public_caller_r01", RUNNER)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load the one-shot caller harness")
HARNESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HARNESS)


class FixtureServerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="agent-interface-fixture-test-")
        root = Path(self.temp.name)
        (self.server, self.thread, self.posts, self.lock, self.page_ready,
         self.ready_records) = HARNESS.make_fixture_server(
             root / "posts.json", root / "ready.json")
        self.base = f"http://127.0.0.1:{self.server.server_port}"
        self.root = root

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temp.cleanup()

    def test_render_readiness_is_distinct_from_task_submission(self):
        page = urlopen(self.base + "/form", timeout=3).read().decode("utf-8")
        self.assertIn('<input id="token" name="value" form="task"', page)
        self.assertIn("requestAnimationFrame(()=>requestAnimationFrame(()=>fetch('/ready'", page)

        with urlopen(Request(self.base + "/ready", data=b"", method="POST"),
                     timeout=3) as response:
            self.assertEqual(response.status, 204)
            self.assertEqual(response.read(), b"")

        self.assertTrue(self.page_ready.wait(0.1))
        self.assertEqual(len(self.ready_records), 1)
        self.assertEqual(self.ready_records[0]["event"], "render_ready")
        self.assertEqual(json.loads((self.root / "ready.json").read_text())[0]["path"],
                         "/ready")
        self.assertEqual(self.posts, [])

    def test_independent_task_record_contains_only_the_exact_form_post(self):
        body = urlencode({"value": "uictrl-test"}).encode("ascii")
        request = Request(self.base + "/submit", data=body,
                          headers={"Content-Type": "application/x-www-form-urlencoded"},
                          method="POST")
        with urlopen(request, timeout=3) as response:
            result_page = response.read().decode("utf-8")

        self.assertIn("Submission received", result_page)
        self.assertIn("#saved-cue", result_page)
        self.assertEqual(len(self.posts), 1)
        self.assertEqual(self.posts[0]["path"], "/submit")
        self.assertEqual(self.posts[0]["submitted_values"], ["uictrl-test"])
        self.assertEqual(json.loads((self.root / "posts.json").read_text()), self.posts)
        self.assertEqual(self.ready_records, [])


if __name__ == "__main__":
    unittest.main()
