import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent


class ConstructionProtocolTests(unittest.TestCase):
    def test_fixture_separation_and_counts(self):
        train = json.loads((ROOT / "training.json").read_text())
        public = json.loads((ROOT / "public.json").read_text())
        oracle = json.loads((ROOT / "oracle.json").read_text())
        self.assertEqual(len(train["fit"]), 6144)
        self.assertEqual(len(train["validation"]), 3072)
        self.assertEqual(len(public["episodes"]), 72)
        self.assertEqual({x["episode_id"] for x in public["episodes"]},
                         {x["episode_id"] for x in oracle["episodes"]})
        self.assertTrue(all(set(x) == {"episode_id", "signals", "legal", "task_units", "horizon"}
                            for x in public["episodes"]))
        self.assertTrue(all("cohort" in x and "interruptions" in x for x in oracle["episodes"]))

    def test_streaming_policy_protocol(self):
        proc = subprocess.Popen([sys.executable, str(ROOT / "policy.py")], stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)

        def exchange(message):
            proc.stdin.write(json.dumps(message) + "\n")
            proc.stdin.flush()
            return json.loads(proc.stdout.readline())

        try:
            self.assertEqual(exchange({"type": "CALIBRATION", "p_by_signal": {"HIGH": 0.8, "LOW": 0.01},
                                      "base_rate": 0.05, "calibration_pass": True})["type"], "READY")
            self.assertEqual(exchange({"type": "START", "episode_id": "opaque"})["type"], "START_ACK")
            decision = exchange({"type": "TICK", "signal": "HIGH", "legal": True, "progress": 2, "age": 2,
                                 "next_event": 10, "checkpoint_cost": 1, "replay_cost": 2})
            self.assertTrue(decision["checkpoint"])
            self.assertTrue(exchange({"type": "FEEDBACK", "signal": "HIGH", "interrupted": 0})["adaptive_active"])
            blocked = exchange({"type": "TICK", "signal": "HIGH", "legal": False, "progress": 2, "age": 1,
                                "next_event": 10, "checkpoint_cost": 1, "replay_cost": 2})
            self.assertFalse(blocked["checkpoint"])
            self.assertTrue(exchange({"type": "FEEDBACK", "signal": "HIGH", "interrupted": 0})["adaptive_active"])
            self.assertEqual(exchange({"type": "END"})["type"], "END_ACK")
            proc.stdin.write('{"type":"QUIT"}\n')
            proc.stdin.flush()
            proc.stdin.close()
            exit_code = proc.wait(timeout=5)
            stderr = proc.stderr.read()
            proc.stdout.close()
            proc.stderr.close()
            self.assertEqual(exit_code, 0, stderr)
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait(timeout=5)
            if not proc.stdout.closed:
                proc.stdout.close()
            if not proc.stderr.closed:
                proc.stderr.close()


if __name__ == "__main__":
    unittest.main()
