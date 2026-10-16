"""Persistent typed planner boundary for the Codex app-server protocol."""
from dataclasses import dataclass
import json
from pathlib import Path
import threading


class PlannerProtocolError(RuntimeError):
    pass


@dataclass(frozen=True)
class TurnHandle:
    session_generation: int
    thread_id: str
    turn_id: str


@dataclass(frozen=True)
class TurnResult:
    handle: TurnHandle
    status: str
    answer_eligible: bool
    answer: object
    error: str | None
    usage: object
    cancellation_requested: bool
    completed_agent_messages: int


class PersistentPlannerAdapter:
    """Own one planner thread and enforce an observation-to-answer lifecycle."""

    def __init__(self, client, *, model, effort, cwd, base_instructions,
                 thread_config=None):
        self.client = client
        self.model = model
        self.effort = effort
        self.cwd = str(cwd)
        self.base_instructions = base_instructions
        self.thread_config = {"project_doc_max_bytes": 0} if thread_config is None else thread_config
        self._lock = threading.Lock()
        self._generation = 0
        self._thread_id = None
        self._active = None
        self._terminal_status = None
        self._cancellation_requested = False
        self._interrupt_response = None

    @property
    def thread_id(self):
        with self._lock:
            return self._thread_id

    def start_session(self):
        with self._lock:
            if self._active is not None and self._terminal_status is None:
                raise PlannerProtocolError("cannot replace a session with an active turn")
        response = self.client.start_thread(
            model=self.model,
            cwd=self.cwd,
            approvalPolicy="never",
            sandbox="read-only",
            config=self.thread_config,
            baseInstructions=self.base_instructions,
            ephemeral=True,
            threadSource="exec",
        )
        thread_id = response.get("thread", {}).get("id")
        if not thread_id:
            raise PlannerProtocolError("thread/start returned no thread id")
        with self._lock:
            self._generation += 1
            self._thread_id = thread_id
            self._active = None
            self._terminal_status = None
            self._cancellation_requested = False
            self._interrupt_response = None
            return thread_id

    def begin_turn(self, prompt, *, output_schema, image_path=None):
        with self._lock:
            if self._thread_id is None:
                raise PlannerProtocolError("start_session must be called first")
            if self._active is not None and self._terminal_status is None:
                raise PlannerProtocolError("only one turn may be active per planner session")
            thread_id = self._thread_id
            generation = self._generation
        inputs = [{"type": "text", "text": prompt, "text_elements": []}]
        if image_path is not None:
            inputs.append({"type": "localImage", "path": str(Path(image_path))})
        response = self.client.start_turn(
            thread_id, inputs, model=self.model, effort=self.effort,
            outputSchema=output_schema)
        turn_id = response.get("turn", {}).get("id")
        if not turn_id:
            raise PlannerProtocolError("turn/start returned no turn id")
        handle = TurnHandle(generation, thread_id, turn_id)
        with self._lock:
            if self._thread_id != thread_id or self._generation != generation:
                raise PlannerProtocolError("session changed while turn/start was pending")
            self._active = handle
            self._terminal_status = None
            self._cancellation_requested = False
            self._interrupt_response = None
            self._output_schema = output_schema
        return handle

    def interrupt(self, handle):
        with self._lock:
            self._require_active(handle)
            if self._terminal_status is not None:
                return {"outcome": "already_terminal", "status": self._terminal_status}
            if self._cancellation_requested:
                return {"outcome": "already_requested", "response": self._interrupt_response}
            # This flag is the semantic boundary: any later answer belongs to a
            # stale observation even if server completion wins the wire race.
            self._cancellation_requested = True
        try:
            response = self.client.interrupt_turn(handle.thread_id, handle.turn_id)
        except Exception as error:
            response = {"error": repr(error)}
            outcome = "request_error"
        else:
            outcome = "requested"
        with self._lock:
            self._interrupt_response = response
        return {"outcome": outcome, "response": response}

    def await_turn(self, handle, timeout=120):
        with self._lock:
            self._require_active(handle)
        completed = self.client.wait_turn_completed(
            handle.thread_id, handle.turn_id, timeout=timeout)
        turn = completed.get("turn", {})
        status = turn.get("status")
        if not status:
            raise PlannerProtocolError("turn/completed returned no status")
        with self._lock:
            self._require_active(handle)
            self._terminal_status = status
            cancelled = self._cancellation_requested

        usage = self.client.latest_turn_usage(handle.thread_id, handle.turn_id)
        messages = [item for item in turn.get("items", [])
                    if item.get("type") == "agentMessage"]
        answer = None
        error = None
        eligible = False
        if status != "completed":
            error = f"turn status is {status}"
        elif cancelled:
            error = "answer belongs to an invalidated observation"
        elif len(messages) != 1:
            error = f"expected one completed agent message, got {len(messages)}"
        elif not isinstance(messages[0].get("text"), str):
            error = "completed agent message has no text"
        else:
            try:
                answer = json.loads(messages[0]["text"])
            except json.JSONDecodeError as parse_error:
                error = f"invalid JSON answer: {parse_error.msg}"
            else:
                try:
                    _validate_schema(answer, self._output_schema)
                except PlannerProtocolError as schema_error:
                    error = str(schema_error)
                    answer = None
                else:
                    eligible = True
        return TurnResult(
            handle=handle, status=status, answer_eligible=eligible, answer=answer,
            error=error, usage=usage, cancellation_requested=cancelled,
            completed_agent_messages=len(messages))

    def _require_active(self, handle):
        if handle != self._active:
            raise PlannerProtocolError("turn handle is not active in this session")


def _validate_schema(value, schema, path="answer"):
    """Validate the strict schema subset used by planner action contracts."""
    if "enum" in schema and value not in schema["enum"]:
        raise PlannerProtocolError(f"{path} is outside enum")
    expected = schema.get("type")
    checks = {
        "object": lambda item: isinstance(item, dict),
        "array": lambda item: isinstance(item, list),
        "string": lambda item: isinstance(item, str),
        "integer": lambda item: isinstance(item, int) and not isinstance(item, bool),
        "number": lambda item: isinstance(item, (int, float)) and not isinstance(item, bool),
        "boolean": lambda item: isinstance(item, bool),
        "null": lambda item: item is None,
    }
    if expected in checks and not checks[expected](value):
        raise PlannerProtocolError(f"{path} must be {expected}")
    if expected == "object":
        properties = schema.get("properties", {})
        missing = [name for name in schema.get("required", []) if name not in value]
        if missing:
            raise PlannerProtocolError(f"{path} is missing required fields: {', '.join(missing)}")
        if schema.get("additionalProperties") is False:
            extra = sorted(set(value) - set(properties))
            if extra:
                raise PlannerProtocolError(f"{path} has extra fields: {', '.join(extra)}")
        for name, item in value.items():
            if name in properties:
                _validate_schema(item, properties[name], f"{path}.{name}")
    elif expected == "array" and "items" in schema:
        for index, item in enumerate(value):
            _validate_schema(item, schema["items"], f"{path}[{index}]")
