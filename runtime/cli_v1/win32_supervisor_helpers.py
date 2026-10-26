"""Native Win32 recovery and readback helpers for the supervised caller."""
from __future__ import annotations

import multiprocessing
import time


def _parse_obligations(obligations):
    if type(obligations) not in (list, tuple):
        raise ValueError("input obligations must be a sequence")
    parsed = {"keys": [], "buttons": [], "unicode": []}
    for item in obligations:
        if type(item) is not str:
            raise ValueError("input obligation must be a string")
        parts = item.split(":")
        if len(parts) == 3 and parts[0] == "key" and parts[1] and parts[2]:
            parsed["keys"].append((parts[1], parts[2]))
        elif len(parts) == 3 and parts[0] == "button" and parts[1] and parts[2]:
            parsed["buttons"].append((parts[1], parts[2]))
        elif len(parts) == 2 and parts[0] == "unicode":
            try:
                unit = int(parts[1], 16)
            except ValueError as error:
                raise ValueError("invalid Unicode obligation") from error
            if not 0 <= unit <= 0xFFFF:
                raise ValueError("invalid Unicode obligation")
            parsed["unicode"].append(unit)
        else:
            raise ValueError("unsupported input obligation")
    if len(set(obligations)) != len(obligations):
        raise ValueError("duplicate input obligation")
    return parsed


def _generation_matches(backend, targets, generation):
    return all(backend.target_generation(target) == generation for target in targets)


def _new_backend(targets):
    from runtime.backends.win32_v1.backend import Win32Backend
    return Win32Backend(targets)


def _recover(request, backend_factory=_new_backend, clock_ns=time.monotonic_ns,
             configured_targets=None):
    required = {"operation_id", "target_generation", "recovery_id", "deadline_ns",
                "obligations"}
    if type(request) is not dict or not required <= set(request):
        raise ValueError("recovery request schema mismatch")
    parsed = _parse_obligations(request["obligations"])
    targets = {target for target, _ in parsed["keys"] + parsed["buttons"]}
    configured_targets = configured_targets or {}
    if not targets and len(configured_targets) == 1 and parsed["unicode"]:
        targets = set(configured_targets)
    if not targets:
        raise ValueError("native recovery requires an attributable input obligation")
    if clock_ns() >= request["deadline_ns"]:
        raise TimeoutError("recovery deadline expired before backend setup")
    configured_targets = configured_targets or {target: target for target in targets}
    if any(target not in configured_targets for target in targets):
        raise ValueError("obligation target is not configured")
    backend = backend_factory({target: configured_targets[target] for target in targets})
    try:
        if not _generation_matches(backend, targets, request["target_generation"]):
            raise RuntimeError("TARGET_GENERATION_CHANGED")
        focus_required = request.get("focus_target_before_release", False)
        if type(focus_required) is not bool:
            raise ValueError("focus requirement must be boolean")
        if focus_required:
            if len(targets) != 1:
                raise ValueError("orphan recovery requires one attributable target")
            focus = getattr(backend, "focus", None)
            if not callable(focus):
                raise RuntimeError("FOREGROUND_FOCUS_UNAVAILABLE")
            focus(next(iter(targets)))
            if clock_ns() >= request["deadline_ns"]:
                raise TimeoutError("recovery deadline expired after target focus")
            if not _generation_matches(backend, targets, request["target_generation"]):
                raise RuntimeError("TARGET_GENERATION_CHANGED")
        for target, key in parsed["keys"]:
            from runtime.backends.win32_v1.backend import virtual_key
            backend.held_keys[key] = virtual_key(key)
            backend.held_key_targets[key] = target
        for target, button in parsed["buttons"]:
            from runtime.backends.win32_v1.backend import BUTTON_FLAGS
            if button not in BUTTON_FLAGS:
                raise ValueError("unsupported button obligation")
            backend.held_buttons.add(button)
            backend.held_button_targets[button] = target
        backend.pending_unicode_ups.update(parsed["unicode"])
        if clock_ns() >= request["deadline_ns"]:
            raise TimeoutError("recovery deadline expired before release")
        release = backend.release_all()
        if clock_ns() >= request["deadline_ns"]:
            raise TimeoutError("recovery deadline expired after release")
        if not _generation_matches(backend, targets, request["target_generation"]):
            raise RuntimeError("TARGET_GENERATION_CHANGED")
        return {"operation_id": request["operation_id"],
                "target_generation": request["target_generation"],
                "recovery_id": request["recovery_id"],
                "release_accepted": (release.get("verified") is True
                    and not backend.pending_unicode_ups),
                "release_receipt": release,
                "pending_unicode_ups": sorted(backend.pending_unicode_ups)}
    finally:
        backend.close()


def _observe(request, backend_factory=_new_backend, clock_ns=time.monotonic_ns,
             configured_targets=None):
    required = {"operation_id", "target_generation", "recovery_id", "deadline_ns",
                "obligations"}
    if type(request) is not dict or not required <= set(request):
        raise ValueError("observer request schema mismatch")
    parsed = _parse_obligations(request["obligations"])
    targets = {target for target, _ in parsed["keys"] + parsed["buttons"]}
    configured_targets = configured_targets or {}
    # An empty obligation set is still observable when there is exactly one
    # configured target: bind the neutral, empty state sample to its generation.
    if not targets and len(configured_targets) == 1:
        targets = set(configured_targets)
    if not targets:
        raise ValueError("native observation requires an attributable input obligation")
    if clock_ns() >= request["deadline_ns"]:
        raise TimeoutError("observer deadline expired before backend setup")
    configured_targets = configured_targets or {target: target for target in targets}
    if any(target not in configured_targets for target in targets):
        raise ValueError("obligation target is not configured")
    backend = backend_factory({target: configured_targets[target] for target in targets})
    try:
        if not _generation_matches(backend, targets, request["target_generation"]):
            raise RuntimeError("TARGET_GENERATION_CHANGED")
        from runtime.backends.win32_v1.backend import BUTTON_FLAGS, virtual_key
        states = []
        for target, key in parsed["keys"]:
            states.append(backend._key_down_state(virtual_key(key), target))
        for target, button in parsed["buttons"]:
            if button not in BUTTON_FLAGS:
                raise ValueError("unsupported button obligation")
            states.append(backend._key_down_state(BUTTON_FLAGS[button][2], target))
        observed_ns = clock_ns()
        if observed_ns >= request["deadline_ns"]:
            raise TimeoutError("observer deadline expired during readback")
        if not _generation_matches(backend, targets, request["target_generation"]):
            raise RuntimeError("TARGET_GENERATION_CHANGED")
        return {"operation_id": request["operation_id"],
                "target_generation": request["target_generation"],
                "recovery_id": request["recovery_id"],
                "neutral": all(state is False for state in states),
                "observed_monotonic_ns": observed_ns,
                "key_button_states": states,
                # Unicode injection is an ordered event pair. It has no
                # persistent virtual-key state for GetAsyncKeyState to query.
                "unicode_event_units": len(parsed["unicode"])}
    finally:
        backend.close()


def _helper_main(kind, targets, connection):
    connection.send({"status": "ready", "helper": kind})
    while True:
        request = connection.recv()
        if request is None:
            return
        try:
            operation = (_recover(request, configured_targets=targets)
                if kind == "recovery" else
                _observe(request, configured_targets=targets))
        except BaseException as error:
            operation = {"operation_id": request.get("operation_id"),
                "target_generation": request.get("target_generation"),
                "recovery_id": request.get("recovery_id"),
                "error_type": type(error).__name__, "error": str(error)[:256],
                "release_accepted": False}
        connection.send(operation)
        connection.send({"control": "operation_complete",
                         "request_id": request.get("request_id")})


def create_native_win32_components(targets, output_directory, *, context=None,
                                   process_identity_reader=None):
    """Construct the opt-in native owner, supervisor helpers and producer."""
    import os
    if os.name != "nt":
        raise OSError("supervised Win32 mode requires Windows")
    from runtime.backends.win32_v1.backend import Win32Backend
    from runtime.cli_v1.owned_win32_session import OwnedWin32SessionOwner
    from runtime.cli_v1.win32_standard_producer import NativeWin32StandardProducerFactory
    from runtime.guarded_win32_v1.operation_owner import OperationOwner
    from runtime.guarded_win32_v1.process_cancellation import OperationCancellationSupervisor
    from runtime.guarded_win32_v1.win32_process_identity import Win32ProcessIdentityReader

    if (type(targets) is not dict or len(targets) != 1
            or any(type(name) is not str or not name or type(hwnd) is not int or hwnd <= 0
                   for name, hwnd in targets.items())):
        raise ValueError("one explicit target name and HWND are required")
    process_identity_reader = process_identity_reader or Win32ProcessIdentityReader()
    operation_owner = OperationOwner(clock_ns=time.monotonic_ns,
        process_identity_reader=process_identity_reader)
    helper_factory = NativeWin32SupervisorHelperFactory(targets, context=context)
    supervisor = OperationCancellationSupervisor(operation_owner,
        recovery_process_factory=lambda: helper_factory("recovery"),
        observer_process_factory=lambda: helper_factory("observer"),
        process_identity_reader=process_identity_reader)
    owner = OwnedWin32SessionOwner(operation_owner, supervisor,
                                   synthetic_only=False)

    def current_generation():
        backend = Win32Backend(targets)
        try:
            return backend.target_generation(next(iter(targets)))
        finally:
            backend.close()

    owner.bind_target_generation_reader(current_generation)
    producer = NativeWin32StandardProducerFactory(targets,
        output_directory, context=context,
        process_identity_reader=process_identity_reader)
    return owner, producer


class NativeWin32SupervisorHelperFactory:
    """Create persistent spawned helpers ready before any producer admission."""

    def __init__(self, targets, *, context=None):
        if type(targets) is not dict or not targets:
            raise ValueError("explicit target map required")
        self._targets = dict(targets)
        self._context = context or multiprocessing.get_context("spawn")

    def __call__(self, kind):
        if kind not in ("recovery", "observer"):
            raise ValueError("unknown Win32 supervisor helper")
        parent, child = self._context.Pipe(duplex=True)
        process = self._context.Process(target=_helper_main,
            args=(kind, self._targets, child), daemon=True)
        return process, parent
