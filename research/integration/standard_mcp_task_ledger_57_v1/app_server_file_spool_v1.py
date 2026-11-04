"""One-shot, network-free handoff from a Linux experiment to a host planner.

The caller and host worker share one evidence directory. Each attempt is
claimed once by moving its request into ``inflight``. A timeout never restores
the request, so an unknown provider outcome cannot be replayed accidentally.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import time
import uuid
from types import SimpleNamespace


_ATTEMPT_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
_STAGES = {"started", "completed", "unknown"}
_MAX_RECORD_BYTES = 1_048_576
_MAX_PROMPT_BYTES = 262_144
_MAX_SCHEMA_BYTES = 262_144
_MAX_IMAGE_BYTES = 25 * 1024 * 1024


class SpoolError(RuntimeError):
    pass


class SpoolOutcomeUnknown(TimeoutError):
    def __init__(self, attempt_id: str, stage: str):
        super().__init__(f"spool attempt {attempt_id} timed out awaiting {stage}; outcome unknown")
        self.attempt_id = attempt_id
        self.stage = stage
        self.outcome = "UNKNOWN"


def _attempt_id(value: str) -> str:
    if not isinstance(value, str) or not _ATTEMPT_ID.fullmatch(value):
        raise ValueError("attempt_id must be a bounded filename-safe identifier")
    return value


def _read_json(path: Path) -> dict:
    try:
        if path.stat().st_size > _MAX_RECORD_BYTES:
            raise SpoolError(f"spool record exceeds {_MAX_RECORD_BYTES} bytes")
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SpoolError(f"invalid spool JSON: {path.name}") from exc
    if not isinstance(value, dict):
        raise SpoolError("spool records must be JSON objects")
    return value


def _canonical_json_sha256(value: dict) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _write_json_atomic_once(path: Path, value: dict) -> None:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if len(encoded.encode("utf-8")) > _MAX_RECORD_BYTES:
        raise ValueError(f"spool record exceeds {_MAX_RECORD_BYTES} bytes")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temp = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(encoded)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        # The persistent marker reserves this attempt/stage before publication.
        marker = path.with_suffix(path.suffix + ".reserved")
        reserve_fd = os.open(marker, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(reserve_fd)
        if path.exists():
            raise FileExistsError(path)
        os.replace(temp, path)
    except BaseException:
        try:
            temp.unlink()
        except FileNotFoundError:
            pass
        raise


def _spool_dirs(root: Path) -> tuple[Path, Path, Path]:
    root = Path(root).resolve()
    requests, inflight, responses = (root / name for name in ("requests", "inflight", "responses"))
    for directory in (requests, inflight, responses):
        directory.mkdir(parents=True, exist_ok=True)
    return requests, inflight, responses


def publish_request(root: Path, *, attempt_id: str, prompt: str,
                    output_schema: dict, image_path: Path,
                    model: str, effort: str) -> dict:
    """Publish one immutable request; duplicate attempt IDs are rejected."""
    attempt_id = _attempt_id(attempt_id)
    if not isinstance(prompt, str) or not prompt:
        raise ValueError("prompt must be a nonempty string")
    if len(prompt.encode("utf-8")) > _MAX_PROMPT_BYTES:
        raise ValueError(f"prompt exceeds {_MAX_PROMPT_BYTES} bytes")
    if not isinstance(output_schema, dict) or not output_schema:
        raise ValueError("output_schema must be a nonempty object")
    if len(json.dumps(output_schema, separators=(",", ":")).encode("utf-8")) > _MAX_SCHEMA_BYTES:
        raise ValueError(f"output_schema exceeds {_MAX_SCHEMA_BYTES} bytes")
    if not isinstance(model, str) or not model or not isinstance(effort, str) or not effort:
        raise ValueError("model and effort must be nonempty strings")
    root = Path(root).resolve()
    image = Path(image_path).resolve(strict=True)
    if not image.is_file() or not image.is_relative_to(root):
        raise ValueError("image must be a regular file inside the shared spool root")
    if image.stat().st_size > _MAX_IMAGE_BYTES:
        raise ValueError(f"image exceeds {_MAX_IMAGE_BYTES} bytes")
    image_rel = image.relative_to(root).as_posix()
    with image.open("rb") as stream:
        image_digest = hashlib.file_digest(stream, "sha256").hexdigest()
    record = {
        "schema": "agent-interface/app-server-spool-request-v1",
        "attempt_id": attempt_id,
        "prompt": prompt,
        "output_schema": output_schema,
        "output_schema_sha256": _canonical_json_sha256(output_schema),
        "image": {"relative_path": image_rel, "sha256": image_digest},
        "model": model,
        "effort": effort,
    }
    requests, inflight, responses = _spool_dirs(root)
    attempt_dir = root / "attempts" / attempt_id
    attempt_dir.mkdir(parents=True, exist_ok=True)
    # The evidence directory may already contain the screenshot. Reserve the
    # attempt there so a second publish cannot reuse the same observation.
    marker = attempt_dir / "request.reserved"
    marker_fd = os.open(marker, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(marker_fd)
    _write_json_atomic_once(requests / f"{attempt_id}.json", record)
    return record


def claim_next(root: Path, *, expected_model: str, expected_effort: str,
               expected_schema_sha256: str) -> dict | None:
    """Atomically move the oldest pending request to inflight exactly once."""
    if (not isinstance(expected_model, str) or not expected_model or
            not isinstance(expected_effort, str) or not expected_effort or
            not re.fullmatch(r"[0-9a-f]{64}", expected_schema_sha256)):
        raise ValueError("host must pin model, effort, and output-schema hash")
    root = Path(root).resolve()
    requests, inflight, _ = _spool_dirs(root)
    for request_path in sorted(requests.glob("*.json"), key=lambda path: path.name):
        attempt_id = _attempt_id(request_path.stem)
        claimed = inflight / request_path.name
        if claimed.exists():
            raise SpoolError("duplicate pending request conflicts with an inflight attempt")
        try:
            os.replace(request_path, claimed)
        except FileNotFoundError:
            continue
        record = _read_json(claimed)
        if (record.get("schema") != "agent-interface/app-server-spool-request-v1" or
                record.get("attempt_id") != attempt_id):
            raise SpoolError("claimed request identity/schema mismatch; request remains inflight")
        if (not isinstance(record.get("prompt"), str) or
                len(record["prompt"].encode("utf-8")) > _MAX_PROMPT_BYTES or
                not isinstance(record.get("output_schema"), dict) or
                len(json.dumps(record["output_schema"], separators=(",", ":")).encode("utf-8")) > _MAX_SCHEMA_BYTES or
                not isinstance(record.get("model"), str) or not record["model"] or
                not isinstance(record.get("effort"), str) or not record["effort"]):
            raise SpoolError("claimed request fields violate the bounded request contract")
        if (record["model"] != expected_model or record["effort"] != expected_effort or
                record.get("output_schema_sha256") != expected_schema_sha256 or
                _canonical_json_sha256(record["output_schema"]) != expected_schema_sha256):
            raise SpoolError("claimed model, effort, or output schema differs from host preregistration")
        image_info = record.get("image")
        if (not isinstance(image_info, dict) or
                not isinstance(image_info.get("relative_path"), str) or
                not re.fullmatch(r"[0-9a-f]{64}", str(image_info.get("sha256", "")))):
            raise SpoolError("claimed request omitted its image reference")
        image = (root / image_info["relative_path"]).resolve(strict=True)
        if not image.is_file() or not image.is_relative_to(root):
            raise SpoolError("claimed image escaped the shared spool root")
        if image.stat().st_size > _MAX_IMAGE_BYTES:
            raise SpoolError(f"claimed image exceeds {_MAX_IMAGE_BYTES} bytes")
        with image.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if digest != image_info.get("sha256"):
            raise SpoolError("claimed image hash mismatch; request remains inflight")
        record["_claimed_path"] = str(claimed)
        record["_image_path"] = str(image)
        return record
    return None


def publish_stage(root: Path, attempt_id: str, stage: str, record: dict) -> None:
    """Publish one start/completion/unknown receipt; stages cannot overwrite."""
    attempt_id = _attempt_id(attempt_id)
    if stage not in _STAGES:
        raise ValueError("stage must be started, completed, or unknown")
    if not isinstance(record, dict):
        raise TypeError("stage record must be an object")
    _, inflight, responses = _spool_dirs(Path(root))
    if not (inflight / f"{attempt_id}.json").is_file():
        raise SpoolError("cannot publish without an inflight claim")
    _write_json_atomic_once(responses / f"{attempt_id}.{stage}.json", {
        "schema": "agent-interface/app-server-spool-response-v1",
        "attempt_id": attempt_id,
        "stage": stage,
        "record": record,
    })


def publish_late_usage(root: Path, attempt_id: str, sequence: int, record: dict) -> None:
    """Publish one immutable, custody-bound usage row after UNKNOWN."""
    attempt_id = _attempt_id(attempt_id)
    if type(sequence) is not int or sequence < 1:
        raise ValueError("late usage sequence must be a positive integer")
    if not isinstance(record, dict):
        raise TypeError("late usage record must be an object")
    _, inflight, responses = _spool_dirs(Path(root))
    if not (inflight / f"{attempt_id}.json").is_file():
        raise SpoolError("cannot publish late usage without an inflight claim")
    if not (responses / f"{attempt_id}.unknown.json").is_file():
        raise SpoolError("late usage requires an immutable UNKNOWN receipt")
    envelope = {
        "schema": "agent-interface/app-server-spool-late-usage-v1",
        "attempt_id": attempt_id,
        "sequence": sequence,
        "record": record,
    }
    encoded = json.dumps(envelope, sort_keys=True, separators=(",", ":"),
                         allow_nan=False).encode("utf-8")
    if len(encoded) > _MAX_RECORD_BYTES:
        raise SpoolError("late usage record exceeds the bounded spool record size")
    _write_json_atomic_once(
        responses / f"{attempt_id}.late-usage-{sequence:06d}.json", envelope)


def wait_for_stage(root: Path, attempt_id: str, stage: str, *, timeout: float) -> dict:
    """Wait without resubmitting; timeout is an explicit UNKNOWN outcome."""
    attempt_id = _attempt_id(attempt_id)
    if stage not in _STAGES or type(timeout) not in (int, float) or timeout <= 0:
        raise ValueError("invalid stage or timeout")
    _, record = wait_for_any_stage(root, attempt_id, (stage,), timeout=timeout)
    return record


def wait_for_any_stage(root: Path, attempt_id: str, stages: tuple[str, ...], *,
                       timeout: float) -> tuple[str, dict]:
    """Wait for the first immutable stage receipt without replaying the request."""
    attempt_id = _attempt_id(attempt_id)
    if (not stages or any(stage not in _STAGES for stage in stages) or
            len(set(stages)) != len(stages) or type(timeout) not in (int, float) or timeout <= 0):
        raise ValueError("invalid stages or timeout")
    _, _, responses = _spool_dirs(Path(root))
    paths = {stage: responses / f"{attempt_id}.{stage}.json" for stage in stages}
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        existing = [stage for stage, path in paths.items() if path.is_file()]
        if len(existing) > 1:
            raise SpoolError("conflicting terminal/start receipts for one attempt")
        if existing:
            stage = existing[0]
            response = _read_json(paths[stage])
            if (response.get("schema") != "agent-interface/app-server-spool-response-v1" or
                    response.get("attempt_id") != attempt_id or response.get("stage") != stage or
                    not isinstance(response.get("record"), dict)):
                raise SpoolError("response identity/schema mismatch")
            return stage, response["record"]
        time.sleep(min(0.01, max(0.0, deadline - time.monotonic())))
    raise SpoolOutcomeUnknown(attempt_id, ",".join(stages))


class FileSpoolPlanner:
    """Container-side planner shim for ``AppServerPublicMcpModelCall``."""

    def __init__(self, root: Path, *, model: str, effort: str,
                 expected_schema_sha256: str, start_timeout: float = 30):
        if not re.fullmatch(r"[0-9a-f]{64}", expected_schema_sha256):
            raise ValueError("expected_schema_sha256 must be a SHA-256 hex digest")
        if type(start_timeout) not in (int, float) or start_timeout <= 0:
            raise ValueError("start_timeout must be positive")
        self.root = Path(root).resolve()
        self.model = model
        self.effort = effort
        self.expected_schema_sha256 = expected_schema_sha256
        self.start_timeout = start_timeout
        self._active = None
        self._admission_pending = False

    def begin_turn(self, prompt, *, output_schema, image_path):
        if self._active is not None or self._admission_pending:
            raise SpoolError("a prior spool turn is active or has an unknown admission outcome")
        if _canonical_json_sha256(output_schema) != self.expected_schema_sha256:
            raise SpoolError("output schema differs from the client preregistration")
        attempt_id = "appserver-" + uuid.uuid4().hex
        self._admission_pending = True
        publish_request(self.root, attempt_id=attempt_id, prompt=prompt,
            output_schema=output_schema, image_path=Path(image_path),
            model=self.model, effort=self.effort)
        stage, record = wait_for_any_stage(self.root, attempt_id,
            ("started", "unknown"), timeout=self.start_timeout)
        if stage == "unknown":
            raise SpoolOutcomeUnknown(attempt_id, "provider start")
        thread_id, turn_id = record.get("thread_id"), record.get("turn_id")
        if not isinstance(thread_id, str) or not thread_id or not isinstance(turn_id, str) or not turn_id:
            raise SpoolError("start receipt omitted provider thread/turn identity")
        self._active = SimpleNamespace(attempt_id=attempt_id,
            thread_id=thread_id, turn_id=turn_id)
        self._admission_pending = False
        return self._active

    def await_turn(self, handle, timeout=120):
        if handle != self._active:
            raise SpoolError("spool turn handle is not active")
        stage, record = wait_for_any_stage(self.root, handle.attempt_id,
            ("completed", "unknown"), timeout=timeout)
        if stage == "unknown":
            raise SpoolOutcomeUnknown(handle.attempt_id, "provider completion")
        if (record.get("thread_id") != handle.thread_id or
                record.get("turn_id") != handle.turn_id):
            raise SpoolError("completion receipt identity differs from start receipt")
        result = SimpleNamespace(
            handle=handle,
            status=record.get("status"),
            answer_eligible=record.get("answer_eligible") is True,
            answer=record.get("answer"),
            error=record.get("error"),
            usage=record.get("usage"),
            cancellation_requested=record.get("cancellation_requested") is True,
            completed_agent_messages=record.get("completed_agent_messages", 0),
        )
        if not isinstance(result.status, str) or type(result.completed_agent_messages) is not int:
            raise SpoolError("completion receipt has malformed terminal fields")
        self._active = None
        return result
