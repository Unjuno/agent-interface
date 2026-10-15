"""Model/vendor-neutral local API over promoted runtime backends."""
from __future__ import annotations

from dataclasses import asdict
from copy import deepcopy
from typing import Any, Mapping

from runtime.selector_v1 import BackendUnavailable, open_session, select_backend

SCHEMA_DOCTOR = "agent-interface/runtime-doctor-v1"
SCHEMA_DISPATCH = "agent-interface/runtime-dispatch-result-v1"


def _program_validation_diagnostic(program):
    """Explain a recorded refusal without changing admission or invoking input."""
    from runtime.core_v1.contract import ContractError, validate_program
    try:
        validate_program(program)
    except ContractError as error:
        detail = str(error)
        # Unsupported operation names can contain arbitrary caller text.
        if detail.startswith('unsupported op '):
            detail = 'unsupported operation'
        diagnostic = {'detail': detail[:256], 'detail_source': 'program_validation'}
        index = getattr(error, 'operation_index', None)
        if type(index) is int and 0 <= index < 128:
            diagnostic['validation_operation_index'] = index
        return diagnostic
    return None


def doctor(*, platform: str | None = None, environ: Mapping[str, str] | None = None,
           check_dependencies: bool = False) -> dict[str, Any]:
    plan = select_backend(platform=platform, environ=environ)
    result = {
        "schema": SCHEMA_DOCTOR,
        "selection": asdict(plan),
        "runtime_available": plan.available,
        "side_effect_authority": False,
        "note": "Selection is diagnostic only; backend manifest and core admission govern effect authority.",
    }
    if check_dependencies:
        from importlib.util import find_spec
        from importlib.metadata import PackageNotFoundError, version
        inventory = []
        for module, distribution, purpose in (
                ('Xlib', 'python-xlib', 'Linux/X11 backend'),
                ('PIL', 'Pillow', 'X11 PNG capture'),
                ('mcp', 'mcp', 'optional MCP transport')):
            entry = {'module': module, 'distribution': distribution, 'purpose': purpose}
            try:
                entry['discoverable'] = find_spec(module) is not None
            except Exception as error:
                entry.update(discoverable=None, discovery_error=repr(error))
            try:
                entry['installed_version'] = version(distribution)
            except PackageNotFoundError:
                entry['installed_version'] = None
            except Exception as error:
                entry.update(installed_version=None, version_error=repr(error))
            inventory.append(entry)
        result['dependency_inventory'] = {
            'scope': 'current_python_environment', 'modules': inventory,
            'note': 'Discovery and package metadata only. Modules are not imported; no display, '
                    'permission, native library or application readiness is verified.'}
    return result


def dispatch(
    program: dict[str, Any],
    targets: Mapping[str, int],
    *,
    current_observation_seq: int,
    current_binding_revision: int,
    display_name: str | None = None,
    capture_directory: str | None = None,
) -> dict[str, Any]:
    return _dispatch(program, targets,
        current_observation_seq=current_observation_seq,
        current_binding_revision=current_binding_revision,
        display_name=display_name, capture_directory=capture_directory)


def dispatch_in_session(session, program: dict[str, Any], *,
                        current_observation_seq: int,
                        current_binding_revision: int,
                        capture_directory: str | None = None) -> dict[str, Any]:
    """Use a caller-owned session; caller serializes use and owns closure.

    No target refresh, recovery reset, authority issuance or concurrency support.
    """
    if session is None or not callable(getattr(session, 'dispatch', None)):
        return {"schema": SCHEMA_DISPATCH, "status": "invalid_request",
                "error": "INVALID_SESSION"}
    return _dispatch(program, {},
        current_observation_seq=current_observation_seq,
        current_binding_revision=current_binding_revision,
        capture_directory=capture_directory, supplied_session=session)


def _dispatch(
    program: dict[str, Any],
    targets: Mapping[str, int],
    *,
    current_observation_seq: int,
    current_binding_revision: int,
    display_name: str | None = None,
    capture_directory: str | None = None,
    supplied_session=None,
) -> dict[str, Any]:
    if type(current_observation_seq) is not int or current_observation_seq < 0:
        return {"schema": SCHEMA_DISPATCH, "status": "invalid_request", "error": "INVALID_OBSERVATION_SEQ"}
    if type(current_binding_revision) is not int or current_binding_revision < 0:
        return {"schema": SCHEMA_DISPATCH, "status": "invalid_request", "error": "INVALID_BINDING_REVISION"}
    if not isinstance(program, dict):
        return {"schema": SCHEMA_DISPATCH, "status": "invalid_request", "error": "PROGRAM_NOT_OBJECT"}
    compilation = None
    operations = program.get('ops')
    from runtime.core_v1.sequence import normalize_observation_regions
    try:
        operations, region_indices = normalize_observation_regions(operations)
    except ValueError as error:
        return {"schema": SCHEMA_DISPATCH, "status": "invalid_request",
                "error": "INVALID_OBSERVATION_REGION", "detail": str(error),
                "source_operation_index": error.operation_index,
                "input_dispatched": False}
    normalization = None
    if region_indices:
        normalization = {'kind': 'explicit_observation_region',
                         'source_program': deepcopy(program),
                         'source_operation_indices': region_indices}
        program = deepcopy(program)
        program['ops'] = operations
    if isinstance(operations, list) and any(isinstance(op, dict) and 'gap_ms' in op for op in operations):
        from runtime.core_v1.sequence import expand_text_gaps
        try:
            expanded, sources = expand_text_gaps(operations)
        except ValueError as error:
            return {"schema": SCHEMA_DISPATCH, "status": "invalid_request",
                    "error": "INVALID_TEXT_GAP", "detail": str(error)}
        compilation = {'kind': 'bounded_text_gap', 'source_program': deepcopy(program),
                       'operation_sources': sources}
        program = deepcopy(program)
        program['ops'] = expanded
    elif isinstance(operations, list) and any(isinstance(op, dict) and 'repeat' in op for op in operations):
        from runtime.core_v1.sequence import expand_key_repeats
        try:
            expanded = expand_key_repeats(operations, max_ops=128)
        except ValueError as error:
            return {"schema": SCHEMA_DISPATCH, "status": "invalid_request",
                    "error": "INVALID_KEY_REPEAT", "detail": str(error)}
        compilation = {'kind': 'bounded_key_repeat', 'source_program': deepcopy(program),
                       'operation_sources': [index for index, op in enumerate(operations)
                                             for _ in range(op.get('repeat', 1))]}
        program = deepcopy(program)
        program['ops'] = expanded
    try:
        session = (supplied_session if supplied_session is not None
                   else open_session(targets, display_name=display_name))
    except BackendUnavailable as error:
        row = {"schema": SCHEMA_DISPATCH, "status": "backend_unavailable", "error": str(error)}
        if normalization is not None:
            row['normalization'] = normalization
        if compilation is not None:
            row['compilation'] = compilation
        return row
    except Exception as error:
        row = {"schema": SCHEMA_DISPATCH, "status": "runtime_failed", "error": repr(error),
               "failure_phase": "backend_initialization"}
        if normalization is not None:
            row['normalization'] = normalization
        if compilation is not None:
            row['compilation'] = compilation
        return row
    row: dict[str, Any] = {}
    try:
        if capture_directory is not None:
            configure = getattr(session.backend, "configure_capture_artifacts", None)
            if not callable(configure):
                raise ValueError("CAPTURE_ARTIFACTS_UNSUPPORTED")
            configure(capture_directory)
        result = session.dispatch(
            program,
            current_observation_seq=current_observation_seq,
            current_binding_revision=current_binding_revision,
        )
        if result.get('status') == 'refused' and result.get('error') == 'INVALID_PROGRAM':
            diagnostic = _program_validation_diagnostic(program)
            if diagnostic is not None:
                result = {**result, **diagnostic}
        row = {"schema": SCHEMA_DISPATCH, "status": "returned", "result": result}
    except Exception as error:
        row = {"schema": SCHEMA_DISPATCH, "status": "runtime_failed", "error": repr(error)}
    finally:
        # This facade closes only sessions it opens. In particular, X11 holds a
        # display connection even if core admission refuses the program.
        close = (getattr(getattr(session, "backend", None), "close", None)
                 if supplied_session is None else None)
        if callable(close):
            try:
                close()
            except Exception as error:
                row["status"] = "runtime_failed"
                row.setdefault("error", "BACKEND_CLOSE_FAILED")
                row["cleanup_error"] = repr(error)
    if compilation is not None:
        row['compilation'] = compilation
    if normalization is not None:
        row['normalization'] = normalization
    return row
