from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import itertools
import json
from pathlib import Path

TASK = "SAFETY-PLANE-DATA-CUTSET-R0-20260919-001"
DECISION_PASS = "PASS_SAFETY_PLANE_DATA_CUTSET_THEOREM_SCOPED"
VERTICES = ("s", "d0", "d1", "a0", "a1", "r")
DATA = ("d0", "d1")
SOURCE = "s"
SINK = "r"
FORWARD_EDGES = tuple(
    (VERTICES[i], VERTICES[j])
    for i in range(len(VERTICES))
    for j in range(i + 1, len(VERTICES))
)
assert len(FORWARD_EDGES) == 15
GRAPH_COUNT = 1 << len(FORWARD_EDGES)


def canonical_json(obj: object) -> bytes:
    return (json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def edges_from_mask(mask: int) -> tuple[tuple[str, str], ...]:
    return tuple(edge for i, edge in enumerate(FORWARD_EDGES) if mask & (1 << i))


def mask_from_edges(edges: set[tuple[str, str]]) -> int:
    index = {edge: i for i, edge in enumerate(FORWARD_EDGES)}
    return sum(1 << index[e] for e in edges)


def reachable(edges: tuple[tuple[str, str], ...], failed: frozenset[str]) -> bool:
    if SOURCE in failed or SINK in failed:
        return False
    adj: dict[str, list[str]] = {v: [] for v in VERTICES}
    for a, b in edges:
        if a not in failed and b not in failed:
            adj[a].append(b)
    seen = {SOURCE}
    stack = [SOURCE]
    while stack:
        cur = stack.pop()
        if cur == SINK:
            return True
        for nxt in adj[cur]:
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return SINK in seen


def data_subsets(max_size: int | None = None):
    for n in range(len(DATA) + 1):
        if max_size is not None and n > max_size:
            continue
        for combo in itertools.combinations(DATA, n):
            yield frozenset(combo)


def oracle_guarantee(edges: tuple[tuple[str, str], ...], k: int | None) -> bool:
    return all(reachable(edges, failed) for failed in data_subsets(k))


def minimum_data_cut(edges: tuple[tuple[str, str], ...]) -> int | None:
    for failed in data_subsets(None):
        if not reachable(edges, failed):
            return len(failed)
    return None


def row_for_mask(mask: int) -> dict[str, object]:
    edges = edges_from_mask(mask)
    min_cut = minimum_data_cut(edges)
    arbitrary_oracle = oracle_guarantee(edges, None)
    arbitrary_theorem = reachable(edges, frozenset(DATA))
    row: dict[str, object] = {
        "mask": mask,
        "base_reachable": reachable(edges, frozenset()),
        "min_data_cut": min_cut,
        "arbitrary_oracle": arbitrary_oracle,
        "arbitrary_theorem": arbitrary_theorem,
    }
    for k in (0, 1, 2):
        row[f"k{k}_oracle"] = oracle_guarantee(edges, k)
        row[f"k{k}_theorem"] = (min_cut is None) or (min_cut > k)
    return row


def directed_controls() -> list[dict[str, object]]:
    controls = [
        (
            "COUPLED_SINGLE_DATA",
            {("s", "d0"), ("d0", "a0"), ("a0", "r")},
            {"min_data_cut": 1, "arbitrary": False, "k0": True, "k1": False, "k2": False},
        ),
        (
            "DIRECT_SAFETY_PATH",
            {("s", "a0"), ("a0", "r")},
            {"min_data_cut": None, "arbitrary": True, "k0": True, "k1": True, "k2": True},
        ),
        (
            "TWO_DATA_ROUTES",
            {
                ("s", "d0"), ("d0", "a0"), ("a0", "r"),
                ("s", "d1"), ("d1", "a1"), ("a1", "r"),
            },
            {"min_data_cut": 2, "arbitrary": False, "k0": True, "k1": True, "k2": False},
        ),
    ]
    out = []
    for name, edges_set, expected in controls:
        mask = mask_from_edges(edges_set)
        row = row_for_mask(mask)
        observed = {
            "min_data_cut": row["min_data_cut"],
            "arbitrary": row["arbitrary_oracle"],
            "k0": row["k0_oracle"],
            "k1": row["k1_oracle"],
            "k2": row["k2_oracle"],
        }
        out.append({"name": name, "mask": mask, "expected": expected, "observed": observed, "pass": observed == expected})
    return out


def summarize(rows: list[dict[str, object]], phase: str) -> dict[str, object]:
    arbitrary_mismatch = sum(r["arbitrary_oracle"] != r["arbitrary_theorem"] for r in rows)
    k_mismatch = {
        str(k): sum(r[f"k{k}_oracle"] != r[f"k{k}_theorem"] for r in rows)
        for k in (0, 1, 2)
    }
    controls = directed_controls()
    complete = len(rows) == GRAPH_COUNT and [r["mask"] for r in rows] == list(range(GRAPH_COUNT))
    counts = {
        "base_reachable": sum(bool(r["base_reachable"]) for r in rows),
        "arbitrary_guarantee": sum(bool(r["arbitrary_oracle"]) for r in rows),
        "k0_guarantee": sum(bool(r["k0_oracle"]) for r in rows),
        "k1_guarantee": sum(bool(r["k1_oracle"]) for r in rows),
        "k2_guarantee": sum(bool(r["k2_oracle"]) for r in rows),
        "min_cut_0": sum(r["min_data_cut"] == 0 for r in rows),
        "min_cut_1": sum(r["min_data_cut"] == 1 for r in rows),
        "min_cut_2": sum(r["min_data_cut"] == 2 for r in rows),
        "min_cut_infinite": sum(r["min_data_cut"] is None for r in rows),
    }
    coverage_ok = complete if phase == "formal" else [r["mask"] for r in rows] == list(range(len(rows)))
    pass_science = coverage_ok and arbitrary_mismatch == 0 and all(v == 0 for v in k_mismatch.values()) and all(c["pass"] for c in controls)
    return {
        "task": TASK,
        "phase": phase,
        "decision": DECISION_PASS if (phase == "formal" and pass_science) else ("PASS_CONSTRUCTION" if pass_science else "FAIL"),
        "pass": pass_science,
        "graph_count": len(rows),
        "expected_graph_count": GRAPH_COUNT if phase == "formal" else len(rows),
        "coverage_exact": complete if phase == "formal" else [r["mask"] for r in rows] == list(range(len(rows))),
        "arbitrary_mismatch": arbitrary_mismatch,
        "k_mismatch": k_mismatch,
        "counts": counts,
        "controls": controls,
        "formal_invocations": 1 if phase == "formal" else 0,
        "reruns": 0,
        "replacements": 0,
        "tuning": 0,
    }


def write_rows(rows: list[dict[str, object]], out: Path) -> dict[str, object]:
    raw = canonical_json(rows)
    gz = gzip.compress(raw, compresslevel=9, mtime=0)
    b64 = base64.b64encode(gz) + b"\n"
    out.write_bytes(b64)
    return {
        "rows_json_sha256": sha256_bytes(raw),
        "rows_gzip_sha256": sha256_bytes(gz),
        "rows_b64_sha256": sha256_bytes(b64),
        "rows_uncompressed_bytes": len(raw),
        "rows_gzip_bytes": len(gz),
        "rows_b64_bytes": len(b64),
    }


def run(phase: str, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    limit = 256 if phase == "construction" else GRAPH_COUNT
    rows = [row_for_mask(mask) for mask in range(limit)]
    summary = summarize(rows, phase)
    row_meta = write_rows(rows, out_dir / ("CONSTRUCTION_ROWS.json.gz.b64" if phase == "construction" else "FORMAL_ROWS.json.gz.b64"))
    summary["row_artifact"] = row_meta
    result_name = "CONSTRUCTION.json" if phase == "construction" else "RESULT.json"
    (out_dir / result_name).write_bytes(canonical_json(summary))
    if not summary["pass"]:
        raise SystemExit(2)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", choices=("construction", "formal"), required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    run(args.phase, Path(args.out_dir))


if __name__ == "__main__":
    main()
