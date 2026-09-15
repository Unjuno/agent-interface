#!/usr/bin/env python3
"""Container compatibility test: existing compiled GUI runtime as a cross-domain local executor."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, random, time
from pathlib import Path

EXPECTED_RUNTIME_BLOB = "0c02db714127c8e0f770f9d4ac03699749899d2b"


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def load_runtime(path: Path):
    data = path.read_bytes()
    actual = git_blob_sha(data)
    if actual != EXPECTED_RUNTIME_BLOB:
        raise RuntimeError(f"runtime blob mismatch: {actual}")
    spec = importlib.util.spec_from_file_location("compiled_gui_interface_v1", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod, actual


def branch(when, outcome, action=None, next_state=None, reason=None):
    return {"when": when, "outcome": outcome, "action": action,
            "next_state": next_state, "reason": reason}


def surface_symbol():
    return {
        "kind": "target_reference",
        "target_reference": "whole_surface",
        "identity_predicate": "surface_present",
        "dependencies": ["surface_present"],
    }


def continuous_interface():
    return {
        "format": "compiled-gui-interface-v1",
        "interface_id": "continuous-control",
        "session_scope": "container-simulation",
        "surface": "control_surface",
        "predicates": ["surface_present", "zone"],
        "symbols": {"surface": surface_symbol()},
        "actions": {
            "move_left": {
                "target_symbol": "surface",
                "operation": "bounded_left",
                "expected_effect": {"surface_present": True},
            },
            "move_right": {
                "target_symbol": "surface",
                "operation": "bounded_right",
                "expected_effect": {"surface_present": True},
            },
        },
        "method": {
            "name": "center",
            "version": "1",
            "initial_state": "steer",
            "max_transitions": 16,
            "max_runtime_ms": 1000,
            "states": {
                "steer": {"branches": [
                    branch({"surface_present": False}, "yield",
                           reason="association_changed"),
                    branch({"surface_present": True, "zone": "RIGHT"},
                           "action", "move_left", "steer"),
                    branch({"surface_present": True, "zone": "LEFT"},
                           "action", "move_right", "steer"),
                    branch({"surface_present": True, "zone": "GOAL"},
                           "complete"),
                ]},
            },
        },
    }


def desktop_interface():
    return {
        "format": "compiled-gui-interface-v1",
        "interface_id": "desktop-two-step",
        "session_scope": "container-simulation",
        "surface": "desktop_surface",
        "predicates": ["surface_present", "stage"],
        "symbols": {"surface": surface_symbol()},
        "actions": {
            "enter_token": {
                "target_symbol": "surface",
                "operation": "enter_token",
                "expected_effect": {"surface_present": True, "stage": "BLUE"},
            },
            "confirm": {
                "target_symbol": "surface",
                "operation": "confirm",
                "expected_effect": {"surface_present": True, "stage": "GREEN"},
            },
        },
        "method": {
            "name": "submit",
            "version": "1",
            "initial_state": "token",
            "max_transitions": 4,
            "max_runtime_ms": 1000,
            "states": {
                "token": {"branches": [
                    branch({"surface_present": False}, "yield",
                           reason="association_changed"),
                    branch({"surface_present": True, "stage": "RED"},
                           "action", "enter_token", "confirm_state"),
                ]},
                "confirm_state": {"branches": [
                    branch({"surface_present": False}, "yield",
                           reason="association_changed"),
                    branch({"surface_present": True, "stage": "BLUE"},
                           "action", "confirm", "done"),
                    branch({"surface_present": True, "stage": "YELLOW"},
                           "yield", reason="association_changed"),
                ]},
                "done": {"branches": [
                    branch({"surface_present": True, "stage": "GREEN"},
                           "complete"),
                    branch({"surface_present": False}, "yield",
                           reason="association_changed"),
                ]},
            },
        },
    }


class Simulation:
    def __init__(self, domain, *, x=0, vanish_after=None, changed=False):
        self.domain = domain
        self.x = x
        self.present = True
        self.stage = "RED"
        self.sequence = 0
        self.actions = 0
        self.vanish_after = vanish_after
        self.changed = changed
        self.score = 0

    def predicates(self):
        if self.domain == "continuous":
            zone = "GOAL" if self.x == 0 else ("RIGHT" if self.x > 0 else "LEFT")
            return {"surface_present": self.present, "zone": zone}
        return {"surface_present": self.present, "stage": self.stage}

    def observe(self, _request):
        self.sequence += 1
        predicates = self.predicates()
        digest = hashlib.sha256(
            json.dumps([self.sequence, predicates], sort_keys=True).encode()
        ).hexdigest()[:16]
        return {
            "sequence": self.sequence,
            "captured_ns": time.perf_counter_ns(),
            "surface": "control_surface" if self.domain == "continuous"
                       else "desktop_surface",
            "predicates": predicates,
            "evidence_ref": f"e{self.sequence}",
            "evidence_digest": digest,
        }

    def admit(self, request):
        eligible = self.present and request["observation"]["sequence"] == self.sequence
        return {
            "eligible": eligible,
            "status": "revalidated" if eligible else "missing",
            "authorization": f"a{self.sequence}" if eligible else None,
            "expected_sequence": self.sequence,
            "valid_until_ns": time.perf_counter_ns() + 100_000_000,
        }

    def execute(self, request):
        self.actions += 1
        operation = request["operation"]
        if self.domain == "continuous":
            if operation == "bounded_left":
                self.x -= 1
            elif operation == "bounded_right":
                self.x += 1
            if self.vanish_after is not None and self.actions >= self.vanish_after:
                self.present = False
        else:
            if operation == "enter_token":
                self.stage = "YELLOW" if self.changed else "BLUE"
            elif operation == "confirm":
                self.stage = "GREEN"
                self.score = 1
        return {
            "status": "completed",
            "action_id": f"act{self.actions}",
            "effect_ref": f"fx{self.actions}",
            "release": {"verified": True, "keys_down": [], "buttons_down": []},
        }

    @staticmethod
    def verify(request):
        return {"status": "succeeded",
                "evidence_ref": request["observation"]["evidence_ref"]}

    def adapters(self):
        return {
            "observe": self.observe,
            "admit": self.admit,
            "execute": self.execute,
            "verify_effect": self.verify,
            "cancelled": lambda: False,
        }


def run(runtime, episodes: int):
    runtime.validate(continuous_interface())
    runtime.validate(desktop_interface())
    rng = random.Random(20260915)
    result = {
        "continuous_positive": 0,
        "continuous_vanish_safe": 0,
        "desktop_positive": 0,
        "desktop_changed_safe": 0,
        "frontier_resumptions_nonzero": 0,
        "release_failures": 0,
        "failures": [],
        "episodes_per_case": episodes,
    }
    for index in range(episodes):
        x = rng.choice([value for value in range(-8, 9) if value])
        sim = Simulation("continuous", x=x)
        receipt = runtime.run(continuous_interface(), sim.adapters())
        if (receipt["outcome"] == "TASK_SUCCEEDED" and sim.x == 0 and
                1 <= receipt["completed_transitions"] <= 8):
            result["continuous_positive"] += 1
        else:
            result["failures"].append(["continuous_positive", index, x, receipt, sim.x])
        result["frontier_resumptions_nonzero"] += receipt["frontier_model_resumptions"] != 0
        result["release_failures"] += any(
            not transition["release_verified"] for transition in receipt["transitions"])

        vanish_after = rng.randint(1, min(5, abs(x)))
        sim = Simulation("continuous", x=x, vanish_after=vanish_after)
        receipt = runtime.run(continuous_interface(), sim.adapters())
        if (receipt["outcome"] == "SAFE_YIELD" and
                receipt["reason"] in {"effect_failed", "association_changed"} and
                sim.actions == vanish_after):
            result["continuous_vanish_safe"] += 1
        else:
            result["failures"].append(
                ["continuous_vanish", index, x, vanish_after, receipt, sim.actions])
        result["frontier_resumptions_nonzero"] += receipt["frontier_model_resumptions"] != 0
        result["release_failures"] += any(
            not transition["release_verified"] for transition in receipt["transitions"])

    for index in range(episodes):
        sim = Simulation("desktop")
        receipt = runtime.run(desktop_interface(), sim.adapters())
        if (receipt["outcome"] == "TASK_SUCCEEDED" and sim.score == 1 and
                receipt["completed_transitions"] == 2):
            result["desktop_positive"] += 1
        else:
            result["failures"].append(["desktop_positive", index, receipt])
        result["frontier_resumptions_nonzero"] += receipt["frontier_model_resumptions"] != 0
        result["release_failures"] += any(
            not transition["release_verified"] for transition in receipt["transitions"])

        sim = Simulation("desktop", changed=True)
        receipt = runtime.run(desktop_interface(), sim.adapters())
        if (receipt["outcome"] == "SAFE_YIELD" and
                receipt["reason"] == "effect_failed" and sim.score == 0 and
                sim.actions == 1):
            result["desktop_changed_safe"] += 1
        else:
            result["failures"].append(["desktop_changed", index, receipt])
        result["frontier_resumptions_nonzero"] += receipt["frontier_model_resumptions"] != 0
        result["release_failures"] += any(
            not transition["release_verified"] for transition in receipt["transitions"])

    result["pass"] = (
        all(result[key] == episodes for key in (
            "continuous_positive", "continuous_vanish_safe",
            "desktop_positive", "desktop_changed_safe"))
        and result["frontier_resumptions_nonzero"] == 0
        and result["release_failures"] == 0
        and not result["failures"]
    )
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--episodes", type=int, default=2000)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    runtime, runtime_blob = load_runtime(args.runtime)
    result = run(runtime, args.episodes)
    result["schema"] = "compiled-runtime-cross-domain-compat-v1"
    result["runtime_blob"] = runtime_blob
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
