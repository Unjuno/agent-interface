#!/usr/bin/env python3
"""Construction-only synthetic controls for the independent result auditor."""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from audit import validate


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class AuditControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.src = self.root / "src"
        self.inputs = self.root / "inputs"
        self.model = self.root / "model"
        for path in (self.src, self.inputs, self.model):
            path.mkdir()
        (self.src / "PROTOCOL.md").write_text("synthetic protocol\n", encoding="utf-8")
        (self.src / "wheelhouse-manifest.json").write_text("[]\n", encoding="utf-8")
        (self.src / "FREEZE.json").write_text("synthetic freeze\n", encoding="utf-8")
        (self.model / "model.safetensors").write_bytes(b"m" * 1000)
        config = {"dim": 512, "dim_output": 10, "n_layers": 12, "n_heads": 4, "task": "CLASSIFICATION"}
        (self.model / "config.json").write_text(json.dumps(config), encoding="utf-8")
        (self.model / "README.md").write_text("Apache-2.0 test fixture\n", encoding="utf-8")
        (self.inputs / "support.csv").write_text("support fixture\n", encoding="utf-8")
        (self.inputs / "queries.csv").write_text("query fixture\n", encoding="utf-8")
        self.freeze = {
            "allocation": "mitra-gpu-rung0-853-rev4-successor-local-20260927-01",
            "inputs": {
                key: {"sha256": sha(path)}
                for key, path in (
                    ("model", self.model / "model.safetensors"),
                    ("config", self.model / "config.json"),
                    ("model_card", self.model / "README.md"),
                    ("support", self.inputs / "support.csv"),
                    ("queries", self.inputs / "queries.csv"),
                )
            },
            "model": {
                "revision": "edada0d20759c58ada8c8605c25f22f6e98ea5f0",
                "bytes": 1000,
                "config": config,
            },
            "source_sha256": {},
            "wheelhouse_manifest_sha256": sha(self.src / "wheelhouse-manifest.json"),
            "runtime": {"torch_cuda": "12.1", "torch": "2.5.1+cu121"},
        }
        self.p = [1.0 / 6.0] * 6
        self.records = {}
        for phase, count in (("warmup", 16), ("formal", 1024), ("repeat", 16)):
            latency_base = 1.0 if phase != "formal" else 1.0
            self.records[phase] = [
                {
                    "phase": phase,
                    "index": i,
                    "wall_start_unix_ns": i * 3 + 1,
                    "wall_end_unix_ns": i * 3 + 2,
                    "wall_latency_ms": latency_base + (i if phase == "formal" else 0),
                    "cuda_event_ms": 0.1,
                    "process_rchar_delta": 100,
                    "probabilities": self.p,
                    "parameter_devices": ["cuda:0"],
                    "parameter_bytes": 3000,
                    "cuda_memory_allocated_bytes": 4000,
                }
                for i in range(count)
            ]
        self.formal = [[*self.p] for _ in range(1024)]
        self.result = {
            "schema": "issue-4809-mitra-gpu-result-v1",
            "allocation": self.freeze["allocation"],
            "freeze_sha256": sha(self.src / "FREEZE.json"),
            "protocol_sha256": sha(self.src / "PROTOCOL.md"),
            "source_sha256": {},
            "model": {
                "revision": self.freeze["model"]["revision"],
                "sha256": sha(self.model / "model.safetensors"),
                "bytes": 1000,
                "config": self.freeze["model"]["config"],
            },
            "inputs": {
                "support_sha256": sha(self.inputs / "support.csv"),
                "queries_sha256": sha(self.inputs / "queries.csv"),
                "support_rows": 256,
                "query_rows": 1024,
                "class_ids": [f"C{i}" for i in range(6)],
                "feature_ids": [f"f{i}" for i in range(8)],
            },
            "api": {
                "class": "autogluon.tabular.models.mitra.sklearn_interface.MitraClassifier",
                "device": "cuda",
                "fine_tune": False,
                "fine_tune_steps": 0,
                "n_estimators": 1,
                "resident_path": True,
            },
            "optimizer_step_calls": 0,
            "network_expected": "none",
            "runtime": {
                "gpu_name": "NVIDIA GeForce RTX 3080 Laptop GPU",
                "torch_cuda": "12.1",
                "torch": "2.5.1+cu121",
                "autogluon_tabular": "1.6.3",
                "transformers": "5.17.0",
                "huggingface_hub": "1.33.0",
                "safetensors": "0.8.0",
                "torch_threads": 1,
                "gpu_total_memory_bytes": 100000,
                "gpu_free_before_bytes": 80000,
                "gpu_free_after_fit_bytes": 70000,
            },
            "resident_after_fit": {
                "trainer_count": 1,
                "parameter_devices": ["cuda:0"],
                "parameter_bytes": 3000,
                "cuda_memory_allocated_bytes": 4000,
            },
            "cold_model_load_s": 1.0,
            "fit_wall_s": 2.0,
            "context_setup_excluding_load_s": 1.0,
            "peak_rss_bytes": 10000,
            "warmup_probabilities": [[*self.p] for _ in range(16)],
            "formal_probabilities": self.formal,
            "repeat_probabilities": [[*self.p] for _ in range(16)],
            "warmup_records": self.records["warmup"],
            "formal_query_records": self.records["formal"],
            "repeat_records": self.records["repeat"],
            "checkpoint_reread_threshold_bytes": 800,
            "checkpoint_scale_reread_count": 0,
            "latency_summary_ms": {"p50": 512.5, "p95": 972.85, "p99": 1013.77},
            "decision": "REJECT_GPU_HIGH_CADENCE_SHAPE",
        }

    def tearDown(self):
        self.temp.cleanup()

    def test_complete_synthetic_record_passes_structural_gates(self):
        audit = validate(self.result, self.freeze, self.src, self.inputs, self.model)
        self.assertTrue(audit["pass"], audit["errors"])
        self.assertEqual(audit["formal_rows"], 1024)

    def test_zero_cuda_event_is_rejected(self):
        self.result["formal_query_records"][37]["cuda_event_ms"] = 0.0
        audit = validate(self.result, self.freeze, self.src, self.inputs, self.model)
        self.assertIn("per_call_cuda_event:formal:37", audit["errors"])

    def test_optimizer_step_is_rejected(self):
        self.result["optimizer_step_calls"] = 1
        audit = validate(self.result, self.freeze, self.src, self.inputs, self.model)
        self.assertIn("optimizer_steps", audit["errors"])

    def test_checkpoint_reread_is_rejected(self):
        self.result["formal_query_records"][9]["process_rchar_delta"] = 800
        self.result["checkpoint_scale_reread_count"] = 1
        audit = validate(self.result, self.freeze, self.src, self.inputs, self.model)
        self.assertIn("checkpoint_scale_reread_absent", audit["errors"])


if __name__ == "__main__":
    unittest.main()
