#!/usr/bin/env python3
"""Finite deterministic portability/codec experiment.

No GUI, OS-input, model, network, or provider tokenizer is used. The experiment
retains serialization proxies and semantic/conformance outcomes only.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import random
import statistics
import time
from pathlib import Path

from codec import WorkflowDictionary, decode_c0, decode_c1, decode_c2_reference, encode_c0, encode_c1, encode_c2_reference
from contract import OFFICE_FLOOR, admit_program, capability_manifest, office_readiness

WORDS = ["budget", "Q3", "invoice", "meeting", "draft", "review", "alpha", "βeta", "東京"]
TARGETS = ["editor", "spreadsheet", "browser", "mail"]
KEYS = [["CTRL", "S"], ["CTRL", "C"], ["CTRL", "V"], ["CTRL", "Z"], ["ALT", "TAB"]]


def program(pid: str, seq: int, ops: list[dict]) -> dict:
    if not ops or ops[-1].get("op") != "release_all":
        ops = list(ops) + [{"op": "release_all"}]
    return {
        "schema": "agent-interface/program-v0",
        "program_id": pid,
        "source": {"observation_seq": seq, "binding_revision": 1},
        "authority": {"lease_id": "bench-lease", "expires_at_ns": 10**15},
        "ops": ops,
        "terminal": {"release_all_required": True},
    }


def corpus(seed: int, count: int) -> list[dict]:
    rng = random.Random(seed)
    rows = []
    for i in range(count):
        target = rng.choice(TARGETS)
        ops: list[dict] = [{"op": "focus", "target": target}]
        pattern = i % 5
        if pattern == 0:
            ops += [{"op": "text", "text": f"{rng.choice(WORDS)}-{i}"},
                    {"op": "key_chord", "keys": ["CTRL", "S"]}]
        elif pattern == 1:
            ops += [{"op": "key_chord", "keys": rng.choice(KEYS)},
                    {"op": "wait_update", "timeout_ms": 250}]
        elif pattern == 2:
            x, y = rng.randrange(0, 1920), rng.randrange(0, 1080)
            ops += [{"op": "pointer_move", "frame": "screen_physical_px", "x": x, "y": y},
                    {"op": "pointer_button", "button": "left", "down": True},
                    {"op": "pointer_button", "button": "left", "down": False}]
        elif pattern == 3:
            ops += [{"op": "scroll", "dx": 0, "dy": rng.choice([-3, -1, 1, 3])},
                    {"op": "observe", "frame": "window_client", "x": 0, "y": 0, "w": 640, "h": 480}]
        else:
            ops += [{"op": "key_state", "key": "SHIFT", "down": True},
                    {"op": "key_state", "key": "SHIFT", "down": False},
                    {"op": "verify", "predicate": "state_changed"}]
        rows.append(program(f"p{i}", i, ops))
    return rows


def timed_decode(payloads, decoder, repeats=3):
    durations = []
    for _ in range(repeats):
        started = time.perf_counter_ns()
        for payload in payloads:
            decoder(payload)
        durations.append((time.perf_counter_ns() - started) / len(payloads))
    return statistics.median(durations)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--seed", type=int, default=20260915)
    ap.add_argument("--programs", type=int, default=1000)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)

    programs = corpus(args.seed, args.programs)
    c0 = [encode_c0(p) for p in programs]
    c1 = [encode_c1(p) for p in programs]
    if [decode_c0(x) for x in c0] != programs:
        raise AssertionError("C0 corpus roundtrip failure")
    if [decode_c1(x) for x in c1] != programs:
        raise AssertionError("C1 corpus roundtrip failure")

    c0_bytes = [len(x.encode("utf-8")) for x in c0]
    c1_bytes = [len(x.encode("utf-8")) for x in c1]
    codec = {
        "programs": len(programs),
        "c0_total_bytes": sum(c0_bytes),
        "c1_total_bytes": sum(c1_bytes),
        "total_reduction_pct": 100.0 * (1.0 - sum(c1_bytes) / sum(c0_bytes)),
        "median_c0_bytes": statistics.median(c0_bytes),
        "median_c1_bytes": statistics.median(c1_bytes),
        "median_reduction_pct": 100.0 * (1.0 - statistics.median(c1_bytes) / statistics.median(c0_bytes)),
        "c0_decode_ns_per_program_median": timed_decode(c0, decode_c0),
        "c1_decode_ns_per_program_median": timed_decode(c1, decode_c1),
        "roundtrip_failures": 0,
        "provider_token_accounting": "UNAVAILABLE_NO_EXACT_TOKENIZER_OR_PROVIDER_USAGE",
    }

    save_ops = [
        {"op": "focus", "target": "editor"},
        {"op": "key_chord", "keys": ["CTRL", "S"]},
        {"op": "wait_update", "timeout_ms": 250},
        {"op": "verify", "predicate": "document_saved"},
        {"op": "release_all"},
    ]
    dictionary = WorkflowDictionary.build(1, {"save": save_ops})
    definition_bytes = len(dictionary.definition_payload().encode("utf-8"))
    lifecycle = []
    for uses in [1, 2, 4, 8, 16, 32, 64]:
        invocations = [program(f"save{i}", i, save_ops) for i in range(uses)]
        baseline = sum(len(encode_c0(p).encode("utf-8")) for p in invocations)
        references = [encode_c2_reference(p, dictionary, "save") for p in invocations]
        for payload, expected in zip(references, invocations):
            if decode_c2_reference(payload, dictionary) != expected:
                raise AssertionError("C2 roundtrip failure")
        candidate = definition_bytes + sum(len(x.encode("utf-8")) for x in references)
        lifecycle.append({
            "uses": uses,
            "baseline_c0_bytes": baseline,
            "c2_definition_plus_refs_bytes": candidate,
            "delta_bytes": candidate - baseline,
            "candidate_smaller": candidate < baseline,
        })
    first_break_even = next((row["uses"] for row in lifecycle if row["candidate_smaller"]), None)

    full_profiles = {
        os_name: capability_manifest(
            f"synthetic-{os_name}", os_name, backend, OFFICE_FLOOR,
            frames=("screen_physical_px", "screen_logical", "window_client"),
        )
        for os_name, backend in [("linux", "x11"), ("windows", "win32"), ("macos", "quartz")]
    }
    representative = program("portable", 5, [
        {"op": "focus", "target": "editor"},
        {"op": "pointer_move", "frame": "window_client", "x": 10, "y": 20},
        {"op": "pointer_button", "button": "left", "down": True},
        {"op": "pointer_button", "button": "left", "down": False},
        {"op": "text", "text": "office"},
        {"op": "key_chord", "keys": ["CTRL", "S"]},
        {"op": "wait_update", "timeout_ms": 500},
        {"op": "release_all"},
    ])
    admission = {
        name: admit_program(
            representative, manifest, now_ns=1,
            current_observation_seq=5, current_binding_revision=1,
        ).accepted
        for name, manifest in full_profiles.items()
    }

    unimplemented_profiles = {
        os_name: capability_manifest(
            f"unimplemented-{os_name}", os_name, backend, [], unknown=OFFICE_FLOOR,
            frames=("screen_logical",),
        )
        for os_name, backend in [("linux", "wayland"), ("windows", "native"), ("macos", "native")]
    }
    readiness = {name: office_readiness(profile) for name, profile in unimplemented_profiles.items()}

    report = {
        "schema": "agent-interface/runtime-portability-v0-experiment",
        "seed": args.seed,
        "codec": codec,
        "dictionary": {
            "definition_bytes": definition_bytes,
            "digest": dictionary.digest,
            "lifecycle": lifecycle,
            "first_tested_break_even_uses": first_break_even,
        },
        "portable_contract": {
            "same_program_admitted_on_synthetic_full_profiles": admission,
            "unimplemented_profiles_fail_readiness": {k: not v["ready"] for k, v in readiness.items()},
            "note": "synthetic profiles test contract portability only; they are not OS implementation evidence",
        },
        "environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "processor": platform.processor(),
            "cpu_count": os.cpu_count(),
        },
        "claims": {
            "native_os_support": False,
            "provider_token_savings": False,
            "serialization_proxy_reduction": codec["total_reduction_pct"] > 0,
            "semantic_roundtrip": True,
        },
    }
    (args.out / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
