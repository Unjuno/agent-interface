"""Compose retained A09 OCR strings with the source-pinned A07 compiled gate."""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.live_control.integrated_efficiency_compiled_adapter_v2 import (  # noqa: E402
    EXPECTED_METHOD_CONTRACT,
    compile_form_method,
)
from runtime.core_v1.compiled_gui import run as run_compiled  # noqa: E402

A09_PATH = ROOT / "research/integration/compiled_gui_bundle_57_20261004/a09-layout-b-ocr-backend-reproduction/RAW.json"
EXPECTED_A09_SHA256 = "f00088019210ec3d8e4192fd4f4e34816cd689a22d67beb6388d71950ee660b6"
SOURCES = {
    "adapter_v2": (
        "research/live_control/integrated_efficiency_compiled_adapter_v2.py",
        "f1f3f6b2a1f0487a9c6f65b51936fafc8b6101390b1e4070f8e31f741a28b6ef",
    ),
    "compiled_core": (
        "runtime/core_v1/compiled_gui.py",
        "d22160919ad7fc00d8a1c6e1da3240a316b024738362d714fafa68b772005014",
    ),
}
VARIANTS = ("frozen", "candidate", "original_recorded")


def make_interface(task_id: str):
    return compile_form_method(
        interface_id=f"a10-{task_id}",
        session_scope="a10-retained-test-double",
        surface="integrated-form",
        field_handle="field-ref",
        submit_handle="submit-ref",
        method_contract=EXPECTED_METHOD_CONTRACT,
    )


def run_path(task: dict, observer_text: str, evidence_digest: str) -> dict:
    sequence = 0
    action_counter = 0
    actions = []
    release_receipts = []
    effect_verdicts = []
    observations = []
    task_exact = observer_text.strip() == task["expected"]

    def observe(_payload):
        nonlocal sequence
        sequence += 1
        if sequence == 1:
            predicates = {
                "field_pixels_changed": False,
                "field_value_matches_task": False,
                "field_target_present": True,
                "submit_target_present": True,
                "submission_pixels_changed": False,
            }
            evidence_ref = f"{task['id']}/empty"
            digest = hashlib.sha256((evidence_digest + "/empty").encode()).hexdigest()
        elif sequence == 2:
            predicates = {
                "field_pixels_changed": True,
                "field_value_matches_task": task_exact,
                "field_target_present": True,
                "submit_target_present": True,
                "submission_pixels_changed": False,
            }
            evidence_ref = f"{task['id']}/retained-field-frame"
            digest = hashlib.sha256((evidence_digest + "/filled").encode()).hexdigest()
        else:
            predicates = {
                "field_pixels_changed": True,
                "field_value_matches_task": task_exact,
                "field_target_present": True,
                "submit_target_present": True,
                "submission_pixels_changed": "unknown",
            }
            evidence_ref = f"{task['id']}/submit-effect-unavailable"
            digest = hashlib.sha256((evidence_digest + "/submit-effect-unavailable").encode()).hexdigest()
        row = {
            "sequence": sequence,
            "captured_ns": time.perf_counter_ns() - 1_000_000,
            "surface": "integrated-form",
            "predicates": predicates,
            "evidence_ref": evidence_ref,
            "evidence_digest": digest,
        }
        observations.append(row)
        return row

    def admit(payload):
        return {
            "eligible": True,
            "status": "revalidated",
            "authorization": f"one-use-{payload['operation']}-{payload['observation']['sequence']}",
            "expected_sequence": payload["observation"]["sequence"],
            "valid_until_ns": time.perf_counter_ns() + 1_000_000_000,
        }

    def execute(payload):
        nonlocal action_counter
        action_counter += 1
        actions.append(payload["operation"])
        action_id = f"mock-action-{action_counter}"
        release = {"verified": True, "keys_down": [], "buttons_down": []}
        release_receipts.append({"action_id": action_id, **release})
        return {
            "status": "completed",
            "action_id": action_id,
            "effect_ref": f"mock-effect-{action_counter}",
            "release": release,
        }

    def verify_effect(payload):
        if payload["action"] == "submit_form":
            verdict = {"status": "unavailable", "evidence_ref": None}
        else:
            verdict = {
                "status": "succeeded",
                "evidence_ref": payload["observation"]["evidence_ref"],
            }
        effect_verdicts.append({"action": payload["action"], **verdict})
        return verdict

    receipt = run_compiled(
        make_interface(task["id"]),
        {
            "observe": observe,
            "admit": admit,
            "execute": execute,
            "verify_effect": verify_effect,
            "cancelled": lambda: False,
        },
    )
    return {
        "task_id": task["id"],
        "expected": task["expected"],
        "observer_text": observer_text,
        "observer_exact_match": task_exact,
        "observer_evidence_digest": evidence_digest,
        "actions": actions,
        "unique_action_ids": len({row["action_id"] for row in release_receipts}) == len(release_receipts),
        "release_receipts": release_receipts,
        "effect_verdicts": effect_verdicts,
        "observations": observations,
        "receipt": receipt,
    }


def main() -> dict:
    raw_bytes = A09_PATH.read_bytes()
    raw_sha = hashlib.sha256(raw_bytes).hexdigest()
    if raw_sha != EXPECTED_A09_SHA256:
        raise RuntimeError(f"A09 source hash mismatch: {raw_sha}")
    source_hashes = {
        name: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        for name, (path, _expected) in SOURCES.items()
    }
    expected_sources = {name: digest for name, (_path, digest) in SOURCES.items()}
    if source_hashes != expected_sources:
        raise RuntimeError(f"frozen A07 source mismatch: {source_hashes}")

    a09 = json.loads(raw_bytes)
    cases = []
    for row in a09["rows"]:
        for variant in VARIANTS:
            if variant == "original_recorded":
                observer_text = row["original_recorded_ocr"]
                crop = None
            else:
                crop = next(item for item in row["crop_results"] if item["crop"] == variant)
                observer_text = crop["ocr_stdout"]
            digest = hashlib.sha256(
                json.dumps(
                    {
                        "a09_raw_sha256": raw_sha,
                        "case": row["id"],
                        "variant": variant,
                        "source_sha256": row["source_sha256"],
                        "crop_sha256": crop["crop_sha256"] if crop else None,
                        "ocr_stdout": observer_text,
                    },
                    sort_keys=True,
                ).encode()
            ).hexdigest()
            result = run_path(row, observer_text, digest)
            result.update(
                {
                    "variant": variant,
                    "original_task_outcome": row["original_task_outcome"],
                    "source_sha256": row["source_sha256"],
                    "crop_sha256": crop["crop_sha256"] if crop else None,
                    "a09_raw_sha256": raw_sha,
                    "observer_evidence_digest": digest,
                }
            )
            cases.append(result)
    return {
        "schema": "a10_ocr_to_compiled_gate_composition_v1",
        "a09_raw_sha256": raw_sha,
        "source_sha256": source_hashes,
        "plan_sha256": hashlib.sha256(Path(__file__).with_name("PLAN.md").read_bytes()).hexdigest(),
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "scope": "A09 archived OCR strings composed with A07 v2 and compiled core using test-double actions/effects only; no GUI/input/provider/formal allocation",
        "cases": cases,
    }


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))
