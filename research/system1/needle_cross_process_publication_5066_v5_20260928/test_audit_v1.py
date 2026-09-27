import base64
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from audit_v1 import audit


def canonical(seed, generation):
    value = json.loads(json.dumps(seed))
    value["generation"] = generation
    value["provenance"]["seed"] = generation
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def dump_jsonl(path, rows):
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
                    encoding="utf-8")


def fixture(root: Path):
    raw, seed_path = root / "raw", root / "seed.json"
    raw.mkdir()
    seed = {"generation": 3788, "provenance": {"seed": 3788},
            "tensors": {"A": [1.0, -2.0]}}
    seed_bytes = json.dumps(seed, separators=(",", ":")).encode()
    seed_path.write_bytes(seed_bytes)
    atomic = raw / "atomic"
    atomic.mkdir()
    (atomic / "active.json").write_bytes(canonical(seed, 7884))
    replacements = []
    for i in range(4096):
        payload = canonical(seed, 3789 + i)
        replacements.append({"kind": "replace", "replace_index": i,
                             "generation": 3789 + i,
                             "sha256": hashlib.sha256(payload).hexdigest(),
                             "start_ns": i * 10, "end_ns": i * 10 + 2})
    dump_jsonl(atomic / "publisher.jsonl", replacements)
    pids = [101, 202, 303, 404]
    exits = []
    for reader_index, pid in enumerate(pids):
        reads = []
        for j in range(8):
            generation = 3789 + j
            payload = canonical(seed, generation)
            reads.append({"kind": "read", "reader_index": reader_index,
                          "reader_pid": pid, "read_index": j,
                          "open_start_ns": j * 10, "open_end_ns": j * 10 + 3,
                          "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest(),
                          "data_b64": base64.b64encode(payload).decode("ascii"),
                          "generation": generation, "valid": True})
        reads.append({"kind": "reader_exit", "reader_index": reader_index,
                      "reader_pid": pid, "read_count": 8, "exit_ns": 500})
        dump_jsonl(atomic / f"reader-{reader_index}.jsonl", reads)
        exits.append({"reader_index": reader_index, "pid": pid, "exitcode": 0})
    (atomic / "process_exits.json").write_text(json.dumps(exits), encoding="utf-8")
    diagnostic = raw / "diagnostic"
    diagnostic.mkdir()
    candidate = canonical(seed, 3789)
    (diagnostic / "active.json").write_bytes(candidate)
    observations, partial = [], candidate[:len(candidate)//2]
    for i, pid in enumerate(pids):
        row = {"kind": "diagnostic_read", "reader_index": i, "reader_pid": pid,
               "open_start_ns": 1, "open_end_ns": 2, "bytes": len(partial),
               "sha256": hashlib.sha256(partial).hexdigest(), "valid": False,
               "partial_b64": base64.b64encode(partial).decode("ascii")}
        dump_jsonl(diagnostic / f"reader-{i}.jsonl", [row])
        observations.append({"reader_index": i, "pid": pid, "ok": True})
    (diagnostic / "observations.json").write_text(json.dumps(observations), encoding="utf-8")
    return seed_path, raw


class FullAuditTests(unittest.TestCase):
    def test_full_reconstruction_passes(self):
        with tempfile.TemporaryDirectory() as td:
            seed, raw = fixture(Path(td))
            result = audit(seed, raw)
            self.assertEqual(result["errors"], [])
            self.assertEqual(result["overlap_count"], 32)

    def test_auditor_rejects_corrupted_raw_fields(self):
        mutations = ("sha256", "open_start_ns", "reader_pid", "partial_b64", "data_b64")
        for field in mutations:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as td:
                seed, raw = fixture(Path(td))
                if field == "partial_b64":
                    path = raw / "diagnostic" / "reader-0.jsonl"
                else:
                    path = raw / "atomic" / "reader-0.jsonl"
                rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
                rows[0][field] = ("tampered" if field in ("sha256", "partial_b64")
                                  else 999999 if field == "open_start_ns" else 0)
                dump_jsonl(path, rows)
                self.assertTrue(audit(seed, raw)["errors"])


if __name__ == "__main__":
    unittest.main()
