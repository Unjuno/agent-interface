import importlib.util
import shutil
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("source_bound_transform", HERE / "transform.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
audit_spec = importlib.util.spec_from_file_location("source_bound_audit", HERE / "audit.py")
audit = importlib.util.module_from_spec(audit_spec)
audit_spec.loader.exec_module(audit)


class TransformTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        module.reconstruct_sources()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(HERE / "source", ignore_errors=True)

    def test_app_transform_retains_archived_structure_and_adds_parent(self):
        src = (HERE / "source" / "app.py").read_text()
        out = module.transform_app(src)
        self.assertIn("root=tk.Tk()", out)
        self.assertIn("ent.bind('<KeyPress>'", out)
        self.assertIn("causal_parent_ids", out)
        self.assertIn("actuation_id", out)

    def test_observer_transform_retains_archived_loop_and_adds_parent(self):
        src = (HERE / "source" / "observer.py").read_text()
        out = module.transform_observer(src)
        self.assertIn("d.pending_events()", out)
        self.assertIn("actuation_id", out)
        self.assertIn("causal_parent_ids", out)

    def test_app_source_drift_fails_closed(self):
        src = (HERE / "source" / "app.py").read_text().replace("def ev(kind,e):", "def callback(kind,e):")
        with self.assertRaisesRegex(ValueError, "SOURCE_DRIFT"):
            module.transform_app(src)

    def test_observer_missing_event_arm_anchor_fails_closed(self):
        src = (HERE / "source" / "observer.py").read_text().replace("f.write(json.dumps({'seq':seq", "f.write(json.dumps({'new':seq")
        with self.assertRaisesRegex(ValueError, "SOURCE_DRIFT:observer_event_callback"):
            module.transform_observer(src)

    def test_missing_app_callback_anchor_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "expected_1_anchors_got_0"):
            module.replace_exact("def ev(kind,e):\n pass\n", "missing", "new", "test")

    def sample_run(self):
        def event(source, kind, act_id, seq, x_time):
            return {"source": source, "kind": kind, "actuation_id": act_id, "source_seq": seq,
                    "event_id": f"{source}:{seq}", "causal_parent_ids": [f"act:{act_id}"],
                    "keycode": 50, "detail": 50, "time": x_time}
        kinds = (("KeyPress", "epoch:keypress"), ("KeyRelease", "epoch:keyrelease"))
        return {"epoch": "epoch", "app_rows": [event("app", k, a, i, i * 10) for i, (k, a) in enumerate(kinds, 1)],
                "observer_rows": [event("observer", k, a, i, i * 10) for i, (k, a) in enumerate(kinds, 1)],
                "release_attempted": True, "terminal_neutral": True, "error": None}

    def test_independent_audit_accepts_complete_explicit_pair(self):
        status, errors = audit.adjudicate(self.sample_run())
        self.assertEqual(status, "PASS_SOURCE_BOUND_CAUSAL_PAIR")
        self.assertEqual(errors, [])

    def test_observer_missing_event_holds_even_if_neutral(self):
        run = self.sample_run()
        run["observer_rows"] = [r for r in run["observer_rows"] if r["kind"] != "KeyPress"]
        status, errors = audit.adjudicate(run)
        self.assertEqual(status, "HOLD_SOURCE_BOUND_TRACE_INCOMPLETE")
        self.assertIn("OBSERVER_EVENT_SET_MISMATCH", errors)

    def test_missing_release_or_neutrality_holds(self):
        run = self.sample_run()
        run["release_attempted"] = False
        run["terminal_neutral"] = None
        status, errors = audit.adjudicate(run)
        self.assertEqual(status, "HOLD_SOURCE_BOUND_TRACE_INCOMPLETE")
        self.assertIn("CLEANUP_RELEASE_NOT_ATTEMPTED", errors)
        self.assertIn("TERMINAL_NEUTRAL_NOT_PROVEN", errors)


if __name__ == "__main__":
    unittest.main()
