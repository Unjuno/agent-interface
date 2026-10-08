"""Role-separated LoRA study with query-overlapped, newly generated feedback."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import platform
import random
import threading
import time
from pathlib import Path

import torch
import torch.nn.functional as F

from protocol import ALLOCATION, IMAGE_ID, SEEDS, online_window_errors

ARMS = ("SHARED_B_ONLY", "SHARED_A_REPLAY", "ROUTED_SHARED_ADAPTER", "ROUTED_SEPARATE_SKILLS")
SCHEMA = "needle-role-skill-joint-retention-raw-v3-online-window"
ARRIVALS = 16
MICROSTEPS_PER_FEEDBACK = 8
QUERY_BATCH = 256
LEGACY_PATH = Path(__file__).resolve().parent / "lineage/runner.py"
LEGACY_FREEZE_PATH = LEGACY_PATH.with_name("FORMAL_FREEZE.json")
LEGACY_FREEZE_SIDECAR_PATH = LEGACY_PATH.with_name("FORMAL_FREEZE.sha256")
LEGACY_FORMAL_FREEZE_SHA256 = "482449e97f3b399b166da11fe54a2be2b9df1f13fab1e95753b283614a20cd7c"
LEGACY_RUNNER_SHA256 = "0c978c7721da5f42d57a838a3d141c9781a19a981db5d50b8e028183bc14fcdf"


def load_legacy_runner():
    freeze_bytes = LEGACY_FREEZE_PATH.read_bytes().replace(b"\r\n", b"\n")
    if hashlib.sha256(freeze_bytes).hexdigest() != LEGACY_FORMAL_FREEZE_SHA256:
        raise RuntimeError("STOP_LEGACY_FREEZE_SHA256")
    if LEGACY_FREEZE_SIDECAR_PATH.read_bytes().replace(b"\r\n", b"\n") != (LEGACY_FORMAL_FREEZE_SHA256 + "\n").encode("ascii"):
        raise RuntimeError("STOP_LEGACY_FREEZE_SIDECAR")
    source_bytes = LEGACY_PATH.read_bytes().replace(b"\r\n", b"\n")
    if hashlib.sha256(source_bytes).hexdigest() != LEGACY_RUNNER_SHA256:
        raise RuntimeError("STOP_LEGACY_RUNNER_SHA256")
    spec = importlib.util.spec_from_file_location("needle_role_v5_lineage", LEGACY_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("STOP_LEGACY_RUNNER_IMPORT")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


legacy = load_legacy_runner()


def feedback_row(seed: int, arrival: int) -> tuple[torch.Tensor, torch.Tensor]:
    """Generate one and only one new feedback row when the arrival is requested."""
    generator = random.Random(seed * 1009 + 303 + arrival * 7919)
    bit = float(arrival % 2)
    features = [bit, *[generator.random() for _ in range(7)], 1.0]
    x = torch.tensor([features], dtype=torch.float32)
    y = legacy.label_b(x)
    return x, y


def adapter_state(adapter) -> dict:
    return {key: value.detach().cpu().tolist() for key, value in adapter.state_dict().items()}


def adapter_digest(adapter) -> str:
    return hashlib.sha256(legacy.canonical(adapter_state(adapter))).hexdigest()


def clone_adapter(adapter):
    clone = legacy.Adapter()
    with torch.no_grad():
        clone.left.copy_(adapter.left.detach())
        clone.right.copy_(adapter.right.detach())
    clone.eval()
    return clone


def _query_worker(core, adapter_snapshot, probe, query_id, route_receipt,
                  adapter_generation, query_started, first_call_started, stop, box):
    worker_id = f"pid:{os.getpid()}:thread:{threading.get_ident()}"
    start_ns = time.perf_counter_ns()
    query_started.set()
    calls = []
    first = True
    try:
        while not stop.is_set():
            call_start = time.perf_counter_ns()
            with torch.no_grad():
                logits = adapter_snapshot(core, probe)
                prediction = logits.argmax(-1).tolist()
            call_end = time.perf_counter_ns()
            if first:
                first_call_started.set()
                first = False
            calls.append({
                "call_index": len(calls),
                "call_start_ns": call_start,
                "call_end_ns": call_end,
                "prediction_sha256": hashlib.sha256(legacy.canonical(prediction)).hexdigest(),
                "n": int(probe.shape[0]),
            })
            # Give the training thread an opportunity to run without treating
            # the wait itself as an inference interval.
            stop.wait(0.0001)
        box["query"] = {
            "query_id": query_id,
            "worker_id": worker_id,
            "role": "B",
            "scope": legacy.SCOPE,
            "generation": route_receipt["generation"],
            "adapter_generation": adapter_generation,
            "adapter_id": route_receipt["adapter_id"],
            "snapshot": adapter_state(adapter_snapshot),
            "snapshot_sha256": adapter_digest(adapter_snapshot),
            "inference_start_ns": start_ns,
            "inference_end_ns": time.perf_counter_ns(),
            "inference_calls": calls,
        }
    except BaseException as exc:
        box["error"] = f"{type(exc).__name__}:{exc}"
        box["partial_calls"] = calls
        box["query_start_ns"] = start_ns
        box["query_end_ns"] = time.perf_counter_ns()
    finally:
        query_started.set()


def fit_arm_online(arm, seed, core, memory_x, memory_y, test_a, test_b, init):
    shared = arm != "ROUTED_SEPARATE_SKILLS"
    a_adapter, b_adapter = legacy.Adapter(), legacy.Adapter()
    with torch.no_grad():
        for adapter in (a_adapter, b_adapter):
            adapter.left.copy_(torch.tensor(init["left"], dtype=torch.float32))
            adapter.right.copy_(torch.tensor(init["right"], dtype=torch.float32))
    if shared:
        optimizer = torch.optim.AdamW(a_adapter.parameters(), lr=0.04, weight_decay=1e-4)
        b_adapter = a_adapter
    else:
        optimizer = torch.optim.AdamW(b_adapter.parameters(), lr=0.04, weight_decay=1e-4)
    immutable_a = ({key: value.detach().clone() for key, value in a_adapter.state_dict().items()}
                   if not shared else None)
    arrivals, update_ns, routes, yield_controls = [], [], [], []
    queries, feedback, support_rows, support_labels = [], [], [], []
    seen = set()
    route_receipt = legacy.route("B", legacy.SCOPE, 3, 3, separate_skills=not shared) if arm.startswith("ROUTED_") else {
        "status": "READY", "selected_role": "B", "adapter_id": "shared-online-v1",
        "generation": 3, "proposal": None}
    if route_receipt["status"] != "READY":
        raise RuntimeError("STOP_VALID_B_ROUTE_YIELDED")
    selected = b_adapter
    inference_probe = test_b[:QUERY_BATCH]

    for arrival in range(ARRIVALS):
        query_id = f"{seed}:{arm}:q{arrival + 1:02d}"
        feedback_id = f"{seed}:{arm}:f{arrival + 1:02d}"
        snapshot = clone_adapter(selected)
        query_started, first_call_started, stop = threading.Event(), threading.Event(), threading.Event()
        box: dict[str, object] = {}
        thread = threading.Thread(
            target=_query_worker,
            args=(core, snapshot, inference_probe, query_id, route_receipt,
                  arrival, query_started, first_call_started, stop, box),
            name=f"needle-infer-{seed}-{arm}-{arrival}", daemon=True)
        thread.start()
        if not query_started.wait(timeout=5.0) or not first_call_started.wait(timeout=5.0):
            stop.set()
            thread.join(timeout=5.0)
            raise RuntimeError("STOP_QUERY_START_TIMEOUT")

        # Materialize the feedback row only after the request and first actual
        # inference call have started. It was not present as a support tensor.
        x, y = feedback_row(seed, arrival)
        row = tuple(float(value) for value in x[0].tolist())
        if row in seen:
            stop.set(); thread.join(timeout=5.0)
            raise RuntimeError("STOP_DUPLICATE_ONLINE_FEEDBACK")
        seen.add(row)
        support_rows.append(row)
        support_labels.append(int(y.item()))
        arrived_ns = time.perf_counter_ns()
        trainer_id = f"pid:{os.getpid()}:thread:{threading.get_ident()}"
        started = time.perf_counter_ns()
        consumed_ns = None
        for step in range(MICROSTEPS_PER_FEEDBACK):
            index = arrival * MICROSTEPS_PER_FEEDBACK + step
            bx, by = x.reshape(1, -1), y.reshape(1)
            batch_x, batch_y = legacy.batch_for(arm, bx[0], by[0], memory_x, memory_y, index % 16)
            routes.append(dict(route_receipt))
            step_started = time.perf_counter_ns()
            optimizer.zero_grad(set_to_none=True)
            if consumed_ns is None:
                # Record consumption at the first forward that actually sees
                # the newly arrived feedback row, not at update setup time.
                consumed_ns = time.perf_counter_ns()
            F.cross_entropy(selected(core, batch_x), batch_y).backward()
            optimizer.step()
            update_ns.append(time.perf_counter_ns() - step_started)
        update_end_ns = time.perf_counter_ns()
        stop.set()
        thread.join(timeout=5.0)
        if thread.is_alive():
            raise RuntimeError("STOP_INFERENCE_THREAD_JOIN_TIMEOUT")
        if "error" in box:
            raise RuntimeError("STOP_INFERENCE_WORKER:" + str(box["error"]))
        if consumed_ns is None:
            raise RuntimeError("STOP_FEEDBACK_NEVER_CONSUMED")
        query = box.get("query")
        if not isinstance(query, dict):
            raise RuntimeError("STOP_INFERENCE_QUERY_MISSING")
        queries.append(query)
        feedback.append({
            "feedback_id": feedback_id,
            "query_id": query_id,
            "arrived_ns": arrived_ns,
            "consumed_ns": consumed_ns,
            "update_start_ns": started,
            "update_end_ns": update_end_ns,
            "optimizer_step_start": arrival * MICROSTEPS_PER_FEEDBACK,
            "optimizer_step_count": MICROSTEPS_PER_FEEDBACK,
            "update_total_ns": update_end_ns - started,
            "trainer_worker_id": trainer_id,
            "optimizer_steps": MICROSTEPS_PER_FEEDBACK,
            "feedback_sha256": hashlib.sha256(legacy.canonical(row)).hexdigest(),
        })
        controls = [legacy.route("UNKNOWN", legacy.SCOPE, 3, 3, not shared),
                    legacy.route("B", legacy.SCOPE, 2, 3, not shared),
                    legacy.route("A", "wrong-scope", 3, 3, not shared)]
        yield_controls.append(controls)
        if any(item["status"] != "YIELD" or item["proposal"] is not None for item in controls):
            raise RuntimeError("STOP_INVALID_ROUTE_NOT_YIELDED")
        if immutable_a is not None and any(
                not torch.equal(value, a_adapter.state_dict()[key]) for key, value in immutable_a.items()):
            raise RuntimeError("STOP_A_SKILL_MUTATED")
        state = {"A": {"left": a_adapter.left.detach().tolist(), "right": a_adapter.right.detach().tolist()},
                 "B": {"left": b_adapter.left.detach().tolist(), "right": b_adapter.right.detach().tolist()}}
        role_routes = ([legacy.route("A", legacy.SCOPE, 3, 3, not shared),
                        legacy.route("B", legacy.SCOPE, 3, 3, not shared)] if arm.startswith("ROUTED_") else [])
        arrivals.append({
            "arrival": arrival + 1,
            "skills": state,
            "skills_sha256": legacy.digest(state),
            "yield_controls": controls,
            "role_routes": role_routes,
            "optimizer": legacy.optimizer_state(optimizer, b_adapter),
            "pred_a": legacy.predict(core, a_adapter, test_a),
            "pred_b": legacy.predict(core, b_adapter, test_b),
        })
    record = {"queries": queries, "feedback": feedback}
    errors = online_window_errors(record)
    if errors:
        raise RuntimeError("STOP_ONLINE_WINDOW:" + ";".join(errors))
    return {
        "arm": arm,
        "optimizer_steps": len(update_ns),
        "update_ns": update_ns,
        "routes": routes,
        "yield_controls": yield_controls,
        "arrivals": arrivals,
        "final_optimizer": legacy.optimizer_state(optimizer, b_adapter),
        "a_adapter_immutable": immutable_a is None or all(
            torch.equal(value, a_adapter.state_dict()[key]) for key, value in immutable_a.items()),
        "a_adapter_identity": id(a_adapter) != id(b_adapter) if not shared else id(a_adapter) == id(b_adapter),
        "online_window": record,
        "support_x": [list(row) for row in support_rows],
        "support_y": support_labels,
    }


def run_seed(seed):
    core, train_x, train_y, indices = legacy.train_base(seed)
    for parameter in core.parameters():
        parameter.requires_grad_(False)
    base = legacy.tensor_map(core)
    memory_x, memory_y = legacy.sample(16, seed, 202, 0), None
    memory_y = legacy.label_a(memory_x)
    test_a, test_b = legacy.sample(256, seed, 404, 0), legacy.sample(256, seed, 505, 1)
    torch.manual_seed(seed + 500)
    init = {"left": (torch.randn(16, 2) * 0.1).tolist(), "right": torch.zeros(2, 4).tolist()}
    arms = [fit_arm_online(arm, seed, core, memory_x, memory_y, test_a, test_b, init) for arm in ARMS]
    supports = [(row["support_x"], row["support_y"]) for row in arms]
    if any(value != supports[0] for value in supports[1:]):
        raise RuntimeError("STOP_ARM_FEEDBACK_STREAM_MISMATCH")
    support_x, support_y = supports[0]
    data = {"base_train_x": train_x.tolist(), "base_train_y": train_y.tolist(),
            "base_row_indices": indices, "memory_x": memory_x.tolist(), "memory_y": memory_y.tolist(),
            "support_x": support_x, "support_y": support_y,
            "test_a_x": test_a.tolist(), "test_a_y": legacy.label_a(test_a).tolist(),
            "test_b_x": test_b.tolist(), "test_b_y": legacy.label_b(test_b).tolist()}
    return {
        "seed": seed,
        "base": base,
        "base_sha256": legacy.digest(base),
        "base_after_sha256": legacy.digest(legacy.tensor_map(core)),
        "base_immutable": base == legacy.tensor_map(core),
        "base_train_x": train_x.tolist(), "base_train_y": train_y.tolist(),
        "base_row_indices": indices,
        "memory_x": memory_x.tolist(), "memory_y": memory_y.tolist(),
        "support_x": support_x, "support_y": support_y,
        "test_a_x": test_a.tolist(), "test_a_y": legacy.label_a(test_a).tolist(),
        "test_b_x": test_b.tolist(), "test_b_y": legacy.label_b(test_b).tolist(),
        "dataset_sha256": legacy.dataset_hashes(data),
        "init_adapter": init,
        "arms": arms,
    }


def main():
    output, seed_text = os.environ.get("NEEDLE_OUTPUT", ""), os.environ.get("NEEDLE_SEEDS", "")
    if not output or not seed_text:
        raise SystemExit("STOP_INVALID_TRAINING_ENV")
    try:
        seeds = tuple(int(value) for value in seed_text.split(","))
    except ValueError as exc:
        raise SystemExit("STOP_INVALID_TRAINING_ENV") from exc
    if seeds != SEEDS:
        raise SystemExit("STOP_SEED_ALLOCATION_MISMATCH")
    out = Path(output)
    if not out.is_dir() or any(out.iterdir()):
        raise SystemExit("STOP_OUTPUT_NOT_EMPTY")
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    document = {
        "schema": SCHEMA,
        "allocation": ALLOCATION,
        "seeds": list(SEEDS),
        "arms": list(ARMS),
        "environment": {"platform": platform.platform(), "python": platform.python_version(),
                        "torch": torch.__version__, "device": "cpu", "threads": 1,
                        "interop_threads": 1, "image_id": IMAGE_ID,
                        "network": "none", "pull": "never"},
        "lineage": {"runner_path": str(LEGACY_PATH.relative_to(Path(__file__).resolve().parents[3])),
                    "runner_sha256": LEGACY_RUNNER_SHA256,
                    "formal_freeze_sha256": LEGACY_FORMAL_FREEZE_SHA256},
        "runs": [run_seed(seed) for seed in SEEDS],
    }
    payload = legacy.canonical(document) + b"\n"
    with (out / "formal_result.json").open("xb") as stream:
        stream.write(payload)
    print(json.dumps({"allocation": ALLOCATION, "seeds": list(SEEDS),
                      "formal_result_bytes": len(payload),
                      "formal_result_sha256": legacy.sha(payload)}, sort_keys=True))


if __name__ == "__main__":
    main()
