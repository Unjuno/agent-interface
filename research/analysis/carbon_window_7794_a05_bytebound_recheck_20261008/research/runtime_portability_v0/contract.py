#!/usr/bin/env python3
"""Language-neutral Agent Interface runtime contract reference oracle.

This module is deliberately pure Python and has no OS/GUI side effects. It is
an executable specification for a future systems-language runtime, not the
product ABI itself.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable
import re

SCHEMA_BACKEND = "agent-interface/backend-v0"
SCHEMA_PROGRAM = "agent-interface/program-v0"

CAPTURE_FRAME = "capture.frame"
INPUT_KEYBOARD = "input.keyboard"
INPUT_TEXT = "input.text"
INPUT_POINTER = "input.pointer"
INPUT_SCROLL = "input.scroll"
INPUT_RELEASE_ALL = "input.release_all"
WINDOW_FOCUS = "window.focus"
DISPLAY_GEOMETRY = "display.geometry"
CLOCK_MONOTONIC = "clock.monotonic"
EVENT_FEEDBACK = "event.feedback"
CLIPBOARD_READ = "clipboard.read"
CLIPBOARD_WRITE = "clipboard.write"
WINDOW_ENUMERATE = "window.enumerate"
ACCESSIBILITY_QUERY = "accessibility.query"

KNOWN_CAPABILITIES = frozenset({
    CAPTURE_FRAME, INPUT_KEYBOARD, INPUT_TEXT, INPUT_POINTER, INPUT_SCROLL,
    INPUT_RELEASE_ALL, WINDOW_FOCUS, DISPLAY_GEOMETRY, CLOCK_MONOTONIC,
    EVENT_FEEDBACK, CLIPBOARD_READ, CLIPBOARD_WRITE, WINDOW_ENUMERATE,
    ACCESSIBILITY_QUERY,
})

# Universal office-control floor. Clipboard/accessibility/window enumeration are
# optimizers; the floor remains screenshot + keyboard/pointer/text + focus.
OFFICE_FLOOR = frozenset({
    CAPTURE_FRAME, INPUT_KEYBOARD, INPUT_TEXT, INPUT_POINTER, INPUT_SCROLL,
    INPUT_RELEASE_ALL, WINDOW_FOCUS, DISPLAY_GEOMETRY, CLOCK_MONOTONIC,
    EVENT_FEEDBACK,
})

CAPABILITY_STATES = frozenset({"supported", "unsupported", "unknown", "permission_required"})
OS_NAMES = frozenset({"linux", "windows", "macos"})
COORDINATE_FRAMES = frozenset({"screen_physical_px", "screen_logical", "window_client"})
BUTTONS = frozenset({"left", "middle", "right", "x1", "x2"})
IDENT_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
KEY_RE = re.compile(r"^[A-Za-z0-9._+-]{1,32}$")

ERROR_CODES = frozenset({
    "UNSUPPORTED_CAPABILITY", "PERMISSION_DENIED", "STALE_OBSERVATION",
    "STALE_BINDING", "LEASE_EXPIRED", "FOCUS_MISMATCH",
    "COORDINATE_UNSUPPORTED", "INVALID_PROGRAM", "RELEASE_UNVERIFIED",
    "BACKEND_DISCONNECTED", "CAPTURE_UNAVAILABLE", "EFFECT_UNKNOWN",
})


class ContractError(ValueError):
    """Raised when an object is not valid under the language-neutral contract."""


@dataclass(frozen=True)
class Admission:
    accepted: bool
    error: str | None
    required_capabilities: tuple[str, ...]


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def _int(value: Any, name: str, lo: int, hi: int) -> int:
    _need(type(value) is int, f"{name} must be int")
    _need(lo <= value <= hi, f"{name} out of range [{lo}, {hi}]")
    return value


def _identifier(value: Any, name: str) -> str:
    _need(isinstance(value, str) and bool(IDENT_RE.fullmatch(value)), f"invalid {name}")
    return value


def _key(value: Any) -> str:
    _need(isinstance(value, str) and bool(KEY_RE.fullmatch(value)), "invalid key")
    return value


def validate_backend_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    _need(isinstance(manifest, dict), "manifest must be object")
    _need(manifest.get("schema") == SCHEMA_BACKEND, "backend schema mismatch")
    _identifier(manifest.get("backend_id"), "backend_id")

    platform = manifest.get("platform")
    _need(isinstance(platform, dict), "platform must be object")
    _need(platform.get("os") in OS_NAMES, "unsupported os name")
    _need(isinstance(platform.get("backend"), str) and 1 <= len(platform["backend"]) <= 48,
          "invalid platform backend")

    capabilities = manifest.get("capabilities")
    _need(isinstance(capabilities, dict), "capabilities must be object")
    unknown = set(capabilities) - KNOWN_CAPABILITIES
    _need(not unknown, f"unknown capabilities: {sorted(unknown)}")
    for capability, row in capabilities.items():
        _need(isinstance(row, dict), f"capability {capability} must be object")
        _need(row.get("state") in CAPABILITY_STATES,
              f"invalid state for {capability}")
        detail = row.get("detail", "")
        _need(isinstance(detail, str) and len(detail) <= 256,
              f"invalid detail for {capability}")

    frames = manifest.get("coordinate_frames")
    _need(isinstance(frames, list) and frames, "coordinate_frames must be non-empty list")
    _need(len(frames) == len(set(frames)), "duplicate coordinate frame")
    _need(set(frames) <= COORDINATE_FRAMES, "unknown coordinate frame")

    clock = manifest.get("clock")
    _need(isinstance(clock, dict), "clock must be object")
    _need(clock.get("unit") == "ns", "clock unit must be ns")
    _need(type(clock.get("monotonic")) is bool, "clock.monotonic must be bool")

    permissions = manifest.get("permissions", [])
    _need(isinstance(permissions, list) and all(isinstance(x, str) for x in permissions),
          "permissions must be string list")
    return manifest


def office_readiness(manifest: dict[str, Any]) -> dict[str, Any]:
    validate_backend_manifest(manifest)
    caps = manifest["capabilities"]
    states = {cap: caps.get(cap, {}).get("state", "unknown") for cap in sorted(OFFICE_FLOOR)}
    blocking = [cap for cap, state in states.items() if state != "supported"]
    return {
        "ready": not blocking,
        "blocking_capabilities": blocking,
        "states": states,
    }


def _op_capabilities(op: dict[str, Any]) -> set[str]:
    t = op["op"]
    if t in {"key_chord", "key_state"}:
        return {INPUT_KEYBOARD}
    if t == "text":
        return {INPUT_TEXT}
    if t in {"pointer_move", "pointer_button"}:
        return {INPUT_POINTER, DISPLAY_GEOMETRY}
    if t == "scroll":
        return {INPUT_SCROLL}
    if t == "focus":
        return {WINDOW_FOCUS}
    if t == "observe":
        return {CAPTURE_FRAME, DISPLAY_GEOMETRY}
    if t == "wait_update":
        return {EVENT_FEEDBACK, CLOCK_MONOTONIC}
    if t == "verify":
        return {EVENT_FEEDBACK}
    if t == "release_all":
        return {INPUT_RELEASE_ALL}
    raise ContractError(f"unsupported op {t}")


def validate_program(program: dict[str, Any]) -> dict[str, Any]:
    _need(isinstance(program, dict), "program must be object")
    _need(program.get("schema") == SCHEMA_PROGRAM, "program schema mismatch")
    _identifier(program.get("program_id"), "program_id")

    source = program.get("source")
    _need(isinstance(source, dict), "source must be object")
    _int(source.get("observation_seq"), "source.observation_seq", 0, 2**63 - 1)
    _int(source.get("binding_revision"), "source.binding_revision", 0, 2**63 - 1)

    authority = program.get("authority")
    _need(isinstance(authority, dict), "authority must be object")
    _identifier(authority.get("lease_id"), "lease_id")
    _int(authority.get("expires_at_ns"), "authority.expires_at_ns", 1, 2**63 - 1)

    terminal = program.get("terminal")
    _need(isinstance(terminal, dict), "terminal must be object")
    _need(terminal.get("release_all_required") is True,
          "v0 requires terminal.release_all_required=true")

    ops = program.get("ops")
    _need(isinstance(ops, list) and 1 <= len(ops) <= 128, "ops length out of range")
    _need(ops[-1].get("op") == "release_all", "release_all must be final operation")
    _need(sum(op.get("op") == "release_all" for op in ops if isinstance(op, dict)) == 1,
          "release_all must appear exactly once")

    held_keys: set[str] = set()
    held_buttons: set[str] = set()
    release_seen = False

    for index, op in enumerate(ops):
        _need(isinstance(op, dict), f"op[{index}] must be object")
        t = op.get("op")
        _need(isinstance(t, str), f"op[{index}].op must be string")

        if t == "focus":
            _identifier(op.get("target"), "focus target")
        elif t == "key_chord":
            keys = op.get("keys")
            _need(isinstance(keys, list) and 1 <= len(keys) <= 5, "invalid chord keys")
            normalized = [_key(k) for k in keys]
            _need(len(normalized) == len(set(normalized)), "duplicate key in chord")
        elif t == "key_state":
            key = _key(op.get("key"))
            _need(type(op.get("down")) is bool, "key_state.down must be bool")
            if op["down"]:
                _need(key not in held_keys, f"key {key} already held")
                held_keys.add(key)
            else:
                _need(key in held_keys, f"key {key} released while not held")
                held_keys.remove(key)
        elif t == "text":
            text = op.get("text")
            _need(isinstance(text, str) and len(text) <= 16384, "invalid text")
        elif t == "pointer_move":
            _need(op.get("frame") in COORDINATE_FRAMES, "invalid pointer frame")
            _int(op.get("x"), "pointer x", -1_000_000, 1_000_000)
            _int(op.get("y"), "pointer y", -1_000_000, 1_000_000)
        elif t == "pointer_button":
            button = op.get("button")
            _need(button in BUTTONS, "invalid pointer button")
            _need(type(op.get("down")) is bool, "pointer_button.down must be bool")
            if op["down"]:
                _need(button not in held_buttons, f"button {button} already held")
                held_buttons.add(button)
            else:
                _need(button in held_buttons, f"button {button} released while not held")
                held_buttons.remove(button)
        elif t == "scroll":
            _int(op.get("dx"), "scroll dx", -100_000, 100_000)
            _int(op.get("dy"), "scroll dy", -100_000, 100_000)
        elif t == "observe":
            _need(op.get("frame") in COORDINATE_FRAMES, "invalid observe frame")
            for field in ("x", "y"):
                _int(op.get(field), f"observe {field}", -1_000_000, 1_000_000)
            for field in ("w", "h"):
                _int(op.get(field), f"observe {field}", 1, 1_000_000)
        elif t == "wait_update":
            _int(op.get("timeout_ms"), "wait_update.timeout_ms", 0, 60_000)
        elif t == "verify":
            predicate = op.get("predicate")
            _need(isinstance(predicate, str) and 1 <= len(predicate) <= 512,
                  "invalid verify predicate")
        elif t == "release_all":
            _need(len(op) == 1, "release_all has no arguments")
            held_keys.clear()
            held_buttons.clear()
            release_seen = True
        else:
            raise ContractError(f"unsupported op {t}")

    _need(release_seen, "release_all required")
    _need(not held_keys and not held_buttons, "program terminates with held input")
    return program


def required_capabilities(program: dict[str, Any]) -> tuple[str, ...]:
    validate_program(program)
    required = {INPUT_RELEASE_ALL}
    for op in program["ops"]:
        required |= _op_capabilities(op)
    return tuple(sorted(required))


def admit_program(
    program: dict[str, Any],
    manifest: dict[str, Any],
    *,
    now_ns: int,
    current_observation_seq: int,
    current_binding_revision: int,
) -> Admission:
    try:
        validate_program(program)
        validate_backend_manifest(manifest)
    except ContractError:
        return Admission(False, "INVALID_PROGRAM", tuple())

    required = required_capabilities(program)
    if now_ns > program["authority"]["expires_at_ns"]:
        return Admission(False, "LEASE_EXPIRED", required)
    if program["source"]["observation_seq"] != current_observation_seq:
        return Admission(False, "STALE_OBSERVATION", required)
    if program["source"]["binding_revision"] != current_binding_revision:
        return Admission(False, "STALE_BINDING", required)

    caps = manifest["capabilities"]
    for capability in required:
        state = caps.get(capability, {}).get("state", "unknown")
        if state == "permission_required":
            return Admission(False, "PERMISSION_DENIED", required)
        if state != "supported":
            return Admission(False, "UNSUPPORTED_CAPABILITY", required)

    frames = set(manifest["coordinate_frames"])
    for op in program["ops"]:
        if op["op"] in {"pointer_move", "observe"} and op["frame"] not in frames:
            return Admission(False, "COORDINATE_UNSUPPORTED", required)
    return Admission(True, None, required)


def capability_manifest(
    backend_id: str,
    os_name: str,
    backend: str,
    supported: Iterable[str],
    *,
    permission_required: Iterable[str] = (),
    unknown: Iterable[str] = (),
    frames: Iterable[str] = ("screen_physical_px", "window_client"),
    permissions: Iterable[str] = (),
) -> dict[str, Any]:
    supported_set = set(supported)
    permission_set = set(permission_required)
    unknown_set = set(unknown)
    _need(not (supported_set & permission_set or supported_set & unknown_set or permission_set & unknown_set),
          "capability state sets overlap")
    caps: dict[str, dict[str, str]] = {}
    for capability in sorted(KNOWN_CAPABILITIES):
        if capability in supported_set:
            state = "supported"
        elif capability in permission_set:
            state = "permission_required"
        elif capability in unknown_set:
            state = "unknown"
        else:
            state = "unsupported"
        caps[capability] = {"state": state, "detail": ""}
    result = {
        "schema": SCHEMA_BACKEND,
        "backend_id": backend_id,
        "platform": {"os": os_name, "backend": backend},
        "capabilities": caps,
        "coordinate_frames": list(frames),
        "clock": {"unit": "ns", "monotonic": True},
        "permissions": list(permissions),
    }
    return validate_backend_manifest(result)
