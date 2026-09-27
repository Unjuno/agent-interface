"""Construction-only tests. No trainer/optimizer allocation is invoked."""
import importlib.util
import platform
import unittest
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("needle_study", ROOT / "needle_frontier_study.py")
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)
audit_spec = importlib.util.spec_from_file_location("needle_audit", ROOT / "needle_frontier_audit.py")
audit = importlib.util.module_from_spec(audit_spec)
audit_spec.loader.exec_module(audit)


class Construction(unittest.TestCase):
    def test_all_streams_are_balanced_and_reproducible(self):
        for seed in study.SEEDS:
            for name in study.STREAMS:
                x1, y1 = study.split(seed, name)
                x2, y2 = study.split(seed, name)
                self.assertTrue(torch.equal(x1, x2))
                self.assertTrue(torch.equal(y1, y2))
                self.assertEqual(x1.shape, (256, 8))
                self.assertEqual(int(x1[:, 0].sum()), 128)
                self.assertTrue(torch.equal(y1, x1[:, 0].long() if name != "heldout_B" and name != "support_B" else 1 - x1[:, 0].long()))

    def test_splits_have_no_duplicate_or_cross_split_rows(self):
        for seed in study.SEEDS:
            study.assert_splits_disjoint(seed)

    def test_support_batches_balanced_and_unique(self):
        for seed in study.SEEDS:
            x, y = study.support_batches(seed)
            self.assertEqual(tuple(x.shape), (32, 8, 8))
            self.assertEqual(tuple(y.shape), (32, 8))
            self.assertTrue(all(int(batch[:, 0].sum()) == 4 for batch in x))
            self.assertTrue(torch.equal(y, 1 - x[:, :, 0].long()))

    def test_zero_adapter_is_exact_base_and_base_is_frozen(self):
        torch.manual_seed(400)
        base = study.Net()
        candidate = study.Candidate(base, 401)
        x = torch.rand((17, 8), generator=torch.Generator().manual_seed(402))
        self.assertEqual(int(torch.count_nonzero(candidate.b)), 0)
        self.assertTrue(torch.equal(base(x), candidate(x)))
        self.assertFalse(any(p.requires_grad for p in base.parameters()))

    def test_unknown_scope_and_stale_epoch_yield_without_call(self):
        class NoCall:
            def __call__(self, x):
                raise AssertionError("yield guard must not call model")
        x = torch.zeros((1, 8))
        self.assertEqual(study.guard(NoCall(), x, "unknown", 32)["decision"], "YIELD")
        self.assertEqual(study.guard(NoCall(), x, "B", 31)["decision"], "YIELD")

    def test_independent_auditor_accepts_seeded_no_update_fixture(self):
        runs = []
        for seed in study.SEEDS:
            train_x, train_y = study.split(seed, "train_A")
            xa, ya = study.split(seed, "heldout_A")
            xb, yb = study.split(seed, "heldout_B")
            sx, sy = study.support_batches(seed)
            torch.manual_seed(seed + 1)
            base = study.Net()
            frozen = {k: v.detach().clone() for k, v in base.state_dict().items()}
            candidate = study.Candidate(base, seed + 2)
            snapshots, curve = [], []
            for step in range(33):
                snap = {"a": candidate.a.detach().tolist(), "b": candidate.b.detach().tolist()}
                snapshots.append(snap)
                with torch.no_grad():
                    la, lb, lbase = candidate(xa), candidate(xb), base(xa)
                curve.append({
                    "step": step,
                    "a_correct": int((la.argmax(-1) == ya).sum()),
                    "b_correct": int((lb.argmax(-1) == yb).sum()),
                    "pred_a": la.argmax(-1).tolist(),
                    "pred_b": lb.argmax(-1).tolist(),
                    "ce_a": float(torch.nn.functional.cross_entropy(la, ya)),
                    "ce_b": float(torch.nn.functional.cross_entropy(lb, yb)),
                    "base_a_correct": int((lbase.argmax(-1) == ya).sum()),
                    "n": 256,
                    "logits_a": la.tolist(),
                    "logits_b": lb.tolist(),
                })
            controls = [
                {"decision": "PROPOSAL", "authority": False, "model_calls": 1, "logits": [[0.0] * 4]},
                {"decision": "YIELD", "authority": False, "model_calls": 0, "logits": None},
                {"decision": "YIELD", "authority": False, "model_calls": 0, "logits": None},
            ]
            runs.append({
                "seed": seed, "base_train_steps": 400,
                "base_train_indices": [(i * 17 + seed) % 256 for i in range(400)],
                "base_train_ms": 1.0, "train_x": train_x.tolist(), "train_y": train_y.tolist(),
                "x_a": xa.tolist(), "y_a": ya.tolist(), "x_b": xb.tolist(), "y_b": yb.tolist(),
                "support_x": sx.tolist(), "support_y": sy.tolist(),
                "base_state": study.state_lists(frozen),
                "base_state_sha256": study.tensor_digest(frozen),
                "base_after_sha256": study.tensor_digest(base.state_dict()),
                "curve": curve, "snapshots": snapshots,
                "update_ms": [0.0] * 32, "inference_ms": [0.0] * 33, "controls": controls,
            })
        document = {
            "schema": "needle-online-correction-frontier-v4",
            "runtime": {"image_id": study.IMAGE_ID, "platform": "linux/amd64", "python": platform.python_version(),
                        "torch": torch.__version__, "device": "cpu", "threads": 1, "network": "none"},
            "stream_salts": study.STREAMS, "runs": runs, "authority": False, "input_emissions": 0,
        }
        self.assertEqual(audit.audit_core(document), [])
        outcomes = audit.corruption_controls(document)
        self.assertEqual(len(outcomes), 9)
        self.assertTrue(all(row["rejected"] for row in outcomes), repr(outcomes))


if __name__ == "__main__":
    unittest.main(verbosity=2)
