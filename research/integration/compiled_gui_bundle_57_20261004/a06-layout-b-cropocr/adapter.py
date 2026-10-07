"""Versioned two-layout OCR adapter for the #57 compiled form path.

The historical #7384 client is immutable evidence. This adapter preserves its
layout-A crop and adds a separately pinned layout-B crop/resampling rule.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import time
from pathlib import Path
from typing import Callable

from PIL import Image

from runtime.core_v1.compiled_gui import run as run_compiled


B_LANCZOS = getattr(getattr(Image, "Resampling", Image), "LANCZOS")
LAYOUT_CROP = {
    "A": ((120, 394, 332, 409), (848, 60), None),
    "B": ((495, 541, 803, 577), (1848, 216), B_LANCZOS),
}
TESSERACT_SUFFIX = (
    "stdout",
    "--psm",
    "7",
    "-c",
    "tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyz0123456789-",
)


def read_crop_token(
    image_path: Path,
    layout: str,
    expected_token: str,
    crop_path: Path,
    *,
    tesseract: str = "tesseract",
    runner: Callable = subprocess.run,
) -> dict:
    """Read one declared crop; return unknown on tool/I/O failure."""
    if layout not in LAYOUT_CROP:
        raise ValueError(f"unsupported layout: {layout}")
    box, output_size, resample = LAYOUT_CROP[layout]
    started_ns = time.perf_counter_ns()
    try:
        with Image.open(image_path) as source:
            if source.width < box[2] or source.height < box[3]:
                raise ValueError("source image is smaller than the pinned crop")
            crop = source.convert("RGB").crop(box)
            if resample is None:
                # Keep layout A's historical Pillow resize behavior unchanged.
                crop = crop.resize(output_size)
            else:
                crop = crop.convert("L").resize(output_size, resample=resample)
        crop_path.parent.mkdir(parents=True, exist_ok=True)
        crop.save(crop_path)
        process = runner(
            [tesseract, str(crop_path), *TESSERACT_SUFFIX],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired, TimeoutError) as error:
        return {
            "status": "unknown",
            "exact": None,
            "stdout": "",
            "stderr": str(error),
            "exit": None,
            "elapsed_ns": time.perf_counter_ns() - started_ns,
            "crop_sha256": None,
        }

    stdout = process.stdout or ""
    stderr = process.stderr or ""
    success = process.returncode == 0
    return {
        "status": "completed" if success else "unknown",
        "exact": expected_token == stdout.strip() if success else None,
        "stdout": stdout,
        "stderr": stderr,
        "exit": process.returncode,
        "elapsed_ns": time.perf_counter_ns() - started_ns,
        "crop_sha256": hashlib.sha256(crop_path.read_bytes()).hexdigest(),
    }


def build_interface(aliases: dict, scope: str) -> dict:
    return {
        "format": "compiled-gui-interface-v1",
        "interface_id": "integrated-form-compiled-layout-v2",
        "session_scope": scope,
        "surface": "integrated-form",
        "predicates": ["exact_token_visible", "target_valid", "exact_saved_title"],
        "symbols": {
            kind: {
                "kind": "target_reference",
                "target_reference": aliases[kind],
                "identity_predicate": "target_valid",
                "dependencies": ["target_valid"],
            }
            for kind in ("field", "submit")
        },
        "actions": {
            "enter": {
                "target_symbol": "field",
                "operation": "enter_token",
                "expected_effect": {"exact_token_visible": True},
            },
            "submit": {
                "target_symbol": "submit",
                "operation": "submit_form",
                "expected_effect": {"exact_saved_title": True},
            },
        },
        "method": {
            "name": "enter_then_submit",
            "version": "2",
            "initial_state": "empty",
            "max_transitions": 2,
            "max_runtime_ms": 10000,
            "states": {
                "empty": {
                    "branches": [
                        {
                            "when": {"target_valid": True},
                            "outcome": "action",
                            "action": "enter",
                            "next_state": "filled",
                            "reason": None,
                        }
                    ]
                },
                "filled": {
                    "branches": [
                        {
                            "when": {
                                "exact_token_visible": True,
                                "target_valid": True,
                            },
                            "outcome": "action",
                            "action": "submit",
                            "next_state": "submitted",
                            "reason": None,
                        }
                    ]
                },
                "submitted": {
                    "branches": [
                        {
                            "when": {"exact_saved_title": True},
                            "outcome": "complete",
                            "action": None,
                            "next_state": None,
                            "reason": None,
                        }
                    ]
                },
            },
        },
    }


class CompiledExecution:
    """Bind layout OCR and checked client ports to the existing compiled core.

    The caller must supply the current cancellation state; cancellation is never
    assumed to be false when the adapter is constructed.
    """

    def __init__(
        self,
        client,
        task: dict,
        aliases: dict,
        *,
        cancelled: Callable[[], bool],
        tesseract: str = "tesseract",
        ocr_runner: Callable = subprocess.run,
    ) -> None:
        if not callable(cancelled):
            raise TypeError("a cancellation-state callback is required")
        self.client = client
        self.task = task
        self.aliases = aliases
        self._cancelled_source = cancelled
        self.tesseract = tesseract
        self.ocr_runner = ocr_runner
        self.current = None
        self.authorizations = {}
        self.raw = []
        self.events = []

    def _cancelled(self) -> bool:
        value = self._cancelled_source()
        if type(value) is not bool:
            raise TypeError("cancellation-state callback must return bool")
        return value

    def observe(self, payload: dict) -> dict:
        kind = {"empty": "field", "filled": "submit"}.get(payload["state"])
        if kind:
            check, program = self.client.check(
                self.aliases[kind],
                [12, 19] if kind == "field" else [12, 7],
                "compiled-check-" + kind,
            )
        else:
            program = self.client.submit("compiled-final-observation", [{"op": "observe"}])
            check = None

        observation = program["observations"][-1]
        image_path = self.client.runtime / Path(observation["image"]).name
        crop_path = self.client.root / ("ocr-" + str(observation["sequence"]) + ".png")
        ocr = read_crop_token(
            image_path,
            self.task["layout"],
            self.task["token"],
            crop_path,
            tesseract=self.tesseract,
            runner=self.ocr_runner,
        )
        exact_token_visible = ocr["exact"] if ocr["status"] == "completed" else "unknown"
        image_digest = hashlib.sha256(image_path.read_bytes()).hexdigest()
        title = str(observation.get("context", ""))
        predicates = {
            "exact_token_visible": exact_token_visible,
            "target_valid": bool(
                check
                and check.get("eligible") is True
                and check.get("status") == "VALID"
            ),
            "exact_saved_title": "AI INTEGRATED SAVED" in title,
        }
        clock = self.client.clock()
        if clock["sequence"] != observation["sequence"]:
            raise RuntimeError("observation/clock sequence mismatch")
        self.current = {
            "kind": kind,
            "check": check,
            "clock": clock,
            "observation": observation,
        }
        row = {
            "sequence": observation["sequence"],
            "captured_ns": observation["capture_ns"],
            "surface": "integrated-form",
            "predicates": predicates,
            "evidence_ref": "runtime/" + image_path.name,
            "evidence_digest": hashlib.sha256(
                (image_digest + json.dumps(predicates, sort_keys=True)).encode()
            ).hexdigest(),
        }
        self.raw.append(
            {
                "state": payload["state"],
                "normalized": row,
                "image_sha256": image_digest,
                "target_check": check,
                "raw_observation": observation,
                "ocr": ocr,
            }
        )
        return row

    def admit(self, payload: dict) -> dict:
        row = self.current
        kind = "field" if payload["action"] == "enter" else "submit"
        check = row["check"]
        eligible = bool(
            row["kind"] == kind
            and check
            and check.get("eligible") is True
            and check.get("status") == "VALID"
        )
        sequence = row["clock"]["sequence"]
        deadline = row["clock"]["runtime_ns"] + 3_000_000_000
        token = (
            hashlib.sha256(
                (self.task["task_id"] + payload["action"] + str(sequence)).encode()
            ).hexdigest()
            if eligible
            else None
        )
        if eligible:
            self.authorizations[token] = {
                "action": payload["action"],
                "sequence": sequence,
                "deadline": deadline,
                "used": False,
            }
        return {
            "eligible": eligible,
            "status": "revalidated" if eligible else "missing",
            "authorization": token,
            "expected_sequence": sequence,
            "valid_until_ns": deadline if eligible else 0,
        }

    def execute(self, payload: dict) -> dict:
        authorization = self.authorizations.get(payload["authorization"])
        if (
            not authorization
            or authorization["used"]
            or authorization["action"] != payload["action"]
            or authorization["sequence"] != payload["expected_sequence"]
            or authorization["deadline"] != payload["valid_until_ns"]
        ):
            raise ValueError("invalid local authorization")
        authorization["used"] = True
        kind = "field" if payload["action"] == "enter" else "submit"
        steps = [
            {
                "op": "pointer_click_target",
                "target_handle": self.aliases[kind],
                "offset": [12, 19] if kind == "field" else [12, 7],
                "button": 1,
                "duration_ms": 80,
            }
        ]
        if kind == "field":
            steps.extend(
                [
                    {"op": "chord", "modifier": "Control_L", "key": "a"},
                    {"op": "text", "text": self.task["token"]},
                ]
            )
        steps.append({"op": "settle", "quiet_ms": 80, "timeout_ms": 500})
        result, started, ended = self.client.call(
            {
                "command": {
                    "op": "submit",
                    "expected_sequence": authorization["sequence"],
                    "valid_until_ns": authorization["deadline"],
                    "steps": steps,
                },
                "timeout": 10,
            }
        )
        records = result["reply"]["records"]
        terminal = next(row for row in records if row.get("event") == "terminal")
        self.client.programs.append(
            {
                "label": "compiled-" + payload["action"],
                "started_ns": started,
                "ended_ns": ended,
                "terminal": terminal,
                "observations": [row for row in records if row.get("event") == "observation"],
                "pointer_admissions": [
                    row for row in records if row.get("event") == "pointer_admission"
                ],
                "target_checks": [
                    row for row in records if row.get("event") == "target_handle_checked"
                ],
                "point_mints": [],
            }
        )
        release = terminal["release"]
        return {
            "status": terminal["status"],
            "action_id": terminal["id"],
            "effect_ref": "terminal:" + terminal["id"],
            "release": {
                key: release[key] for key in ("verified", "keys_down", "buttons_down")
            },
        }

    @staticmethod
    def verify(payload: dict) -> dict:
        verdict = all(
            payload["observation"]["predicates"].get(key) == value
            for key, value in payload["expected_effect"].items()
        )
        return {
            "status": "succeeded" if verdict else "failed",
            "evidence_ref": payload["observation"]["evidence_ref"],
        }

    def run(self) -> dict:
        receipt = run_compiled(
            build_interface(self.aliases, self.task["task_id"]),
            {
                "observe": self.observe,
                "admit": self.admit,
                "execute": self.execute,
                "verify_effect": self.verify,
                "cancelled": self._cancelled,
                "journal": self.events.append,
            },
        )
        return {"receipt": receipt, "raw_observations": self.raw, "events": self.events}
