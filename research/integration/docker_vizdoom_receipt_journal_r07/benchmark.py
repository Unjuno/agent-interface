import json
import time
from pathlib import Path

from receipt_journal import ReceiptJournal


PAYLOADS = Path("/payloads")
OUT = Path("/output")
FILES = sorted(PAYLOADS.glob("compiled-*.json"))
VALUES = [(path.name, json.loads(path.read_text(encoding="utf-8")))
          for path in FILES]
if len(VALUES) != 19:
    raise SystemExit(f"expected 19 receipts, got {len(VALUES)}")

methods = ["pretty_files", "persistent_hash_linked_jsonl"]
rows = []
for repetition in range(10):
    order = methods if repetition % 2 == 0 else list(reversed(methods))
    for method in order:
        root = OUT / f"{method}-rep{repetition:02d}"
        root.mkdir(parents=True, exist_ok=False)
        if method == "pretty_files":
            serialize_ns = 0
            write_ns = 0
            started = time.perf_counter_ns()
            for name, value in VALUES:
                before = time.perf_counter_ns()
                text = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
                serialize_ns += time.perf_counter_ns() - before
                before = time.perf_counter_ns()
                (root / name).write_text(text, encoding="utf-8", newline="\n")
                write_ns += time.perf_counter_ns() - before
            append_ns = time.perf_counter_ns() - started
            before = time.perf_counter_ns()
            restored = {
                path.name[:-5]: json.loads(path.read_text(encoding="utf-8"))
                for path in sorted(root.glob("*.json"))
            }
            readback_ns = time.perf_counter_ns() - before
            open_ns = close_ns = 0
        else:
            open_started = time.perf_counter_ns()
            writer = ReceiptJournal(root / "receipts.jsonl")
            open_ns = time.perf_counter_ns() - open_started
            append_started = time.perf_counter_ns()
            references = []
            for name, value in VALUES:
                reference = name[:-5]
                kind = reference.rsplit("-", 1)[-1]
                writer.append(reference, kind, value)
                references.append(reference)
            append_ns = time.perf_counter_ns() - append_started
            close_started = time.perf_counter_ns()
            writer.close()
            close_ns = time.perf_counter_ns() - close_started
            read_started = time.perf_counter_ns()
            reader = ReceiptJournal(root / "receipts.jsonl")
            restored = {reference: reader.lookup(reference) for reference in references}
            reader.close()
            readback_ns = time.perf_counter_ns() - read_started
            serialize_ns = write_ns = None

        if len(restored) != len(VALUES) or any(
                restored[name[:-5]] != value for name, value in VALUES):
            raise RuntimeError(f"payload mismatch: {method} repetition {repetition}")
        total_ns = append_ns + readback_ns + open_ns + close_ns
        bytes_out = sum(path.stat().st_size for path in root.iterdir()
                        if path.is_file())
        rows.append({
            "repetition": repetition,
            "method": method,
            "order_index": order.index(method),
            "records": len(VALUES),
            "open_ns": open_ns,
            "append_ns": append_ns,
            "close_ns": close_ns,
            "readback_ns": readback_ns,
            "total_ns": total_ns,
            "serialize_ns": serialize_ns,
            "write_ns": write_ns,
            "bytes": bytes_out,
            "all_payloads_equal": True,
        })

result = {
    "schema": "agent-interface/receipt-journal-persistent-writer-benchmark-r07",
    "payload_count": len(VALUES),
    "repetitions_per_method": 10,
    "rows": rows,
    "scope": "receipt persistence and verified lookup only; no GUI/input/task effect; per-record flush without fsync; advisory single-writer lock",
}
(OUT / "benchmark-result.json").write_text(
    json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, sort_keys=True))
