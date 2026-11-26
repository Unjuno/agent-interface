"""Opt-in post-load clock and first-input readiness for a private MAP01 session."""
import json
import math
import os
from pathlib import Path
import re
import shutil
import stat
import time


GATE_MAX_AGE_NS = 2_000_000_000
FIRST_PRESS_WINDOW_NS = 1_000_000_000
PASSIVE_STEPS = {"observe", "coast"}


def display_session_proof(session):
    """Match the owned Xvfb child, lock and private cookie used by this session."""
    match = re.fullmatch(r":(1[2-8][0-9])", session.name)
    if match is None or os.environ.get("DISPLAY") != session.name:
        raise ValueError("private Xvfb display required")
    authority = Path(session.auth)
    info = authority.lstat()
    if (os.environ.get("XAUTHORITY") != str(authority)
            or not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o600
            or info.st_uid != os.getuid() or authority.parent != session.tmp):
        raise ValueError("private Xvfb authorization mismatch")
    server = session.xvfb
    expected_server = shutil.which("Xvfb")
    pid = server.pid
    process = Path("/proc") / str(pid)
    if (type(pid) is not int or pid <= 1 or server.poll() is not None
            or Path(f"/tmp/.X{match[1]}-lock").read_text(encoding="ascii").strip() != str(pid)
            or expected_server is None
            or (process / "exe").resolve(strict=True) != Path(expected_server).resolve(strict=True)):
        raise ValueError("owned Xvfb client/lock identity mismatch")
    cgroup = (Path("/proc/self/cgroup").read_text())
    if not cgroup.strip() or (process / "cgroup").read_text() != cgroup:
        raise ValueError("Xvfb left the session control group")
    return {"display": session.name, "xvfb_pid": pid}


def x11_neutral(session):
    keymap = session.d.query_keymap()
    mask = session.d.screen().root.query_pointer().mask
    return len(keymap) == 32 and not any(keymap) and type(mask) is int and mask == 0


class PostLoadGate:
    def __init__(self, output, timeout_seconds, *, clock=time.perf_counter_ns, sleep=time.sleep,
                 display_proof=display_session_proof, neutral=x11_neutral):
        self.path = Path(output) / "post-load-clock-gate.jsonl"
        self.timeout_seconds = timeout_seconds
        self.clock, self.sleep = clock, sleep
        self.display_proof, self.neutral = display_proof, neutral
        self.game = self.session = self.display = self.validated_ns = None
        self.initial_cover_pending = False
        self.initial_cover_accepted = False
        self.first_press = None
        self.first_press_intent = None
        self.first_press_observed = False

    def _state(self):
        for _ in range(5):
            tic = self.game.get_episode_time()
            state = {"tic": tic, "rate": self.game.get_ticrate(),
                     "limit": self.game.get_episode_timeout(),
                     "dead": self.game.is_player_dead(),
                     "finished": self.game.is_episode_finished(),
                     "timeout": self.game.is_episode_timeout_reached()}
            if type(tic) is int and self.game.get_episode_time() == tic:
                return state
        raise ValueError("coherent post-load game clock required")

    def _active_neutral(self):
        state = self._state()
        if (str(self.game.get_mode()) != "Mode.ASYNC_SPECTATOR"
                or type(state["rate"]) is not int or state["rate"] != 35
                or type(state["limit"]) is not int or state["limit"] != 35 * self.timeout_seconds
                or not self.loaded_tic <= state["tic"] < state["limit"] - 175
                or any(state[field] is not False for field in ("dead", "finished", "timeout"))):
            raise ValueError("active post-load spectator clock required")
        last = self.game.get_last_action()
        if (type(last) not in (list, tuple) or len(last) != 9
                or any(type(value) not in (int, float, bool) or not math.isfinite(value) or value != 0
                       for value in last)
                or self.neutral(self.session) is not True):
            raise ValueError("engine action and physical X11 input must be neutral")
        return dict(state, x11_input_neutral=True, last_action=list(last))

    def after_load(self, game, session, *, expected_tic):
        self.game, self.session, self.loaded_tic = game, session, expected_tic
        with self.path.open("x", encoding="utf-8") as stream:
            def record(event, **fields):
                stream.write(json.dumps({"event": event, **fields}, allow_nan=False) + "\n")
                stream.flush()

            try:
                if type(expected_tic) is not int or expected_tic < 0:
                    raise ValueError("exact retained fixture tic required")
                started = self.clock()
                self.display = self.display_proof(session)
                initial = self._active_neutral()
                record("loaded", state=initial, display=self.display, observed_ns=self.clock())
                if initial["tic"] != expected_tic:
                    raise ValueError("loaded game clock disagrees with retained fixture tic")

                def refreshed(series, side):
                    before = self._active_neutral()
                    start_ns = self.clock()
                    self.game.advance_action(1, True)
                    after = self._active_neutral()
                    end_ns = self.clock()
                    record("refresh", series=series, side=side, requested_tics=1, update_state=True,
                           before=before, after=after, start_ns=start_ns, end_ns=end_ns)
                    return after["tic"], end_ns

                def pair(series, seconds):
                    left, left_ns = refreshed(series, "left")
                    wait_start = self.clock()
                    if seconds:
                        self.sleep(seconds)
                    waited = self.clock() - wait_start
                    right, right_ns = refreshed(series, "right")
                    return right - left, right_ns - left_ns, waited

                immediate, _, immediate_wait = pair("immediate", 0)
                delayed, delayed_elapsed, delayed_wait = pair("delayed", 2)
                finish_ns = self.clock()
                if (not 0 <= immediate <= 5 or not 0 <= immediate_wait < 100_000_000
                        or delayed_wait < 1_950_000_000 or delayed_elapsed <= 0
                        or delayed - 2 < 35 or delayed - immediate < 35
                        or not 25 <= delayed * 1e9 / delayed_elapsed <= 45
                        or finish_ns - started > 5_000_000_000
                        or self.display_proof(session) != self.display):
                    raise ValueError("post-load spectator clock did not qualify")
                evidence = {"passed": True, "validated_ns": finish_ns,
                            "immediate_delta": immediate, "delayed_delta": delayed,
                            "delayed_elapsed_ns": delayed_elapsed, "grants_input_authority": False}
                record("gate", **evidence)
                self.validated_ns = finish_ns
                return evidence
            except BaseException as error:
                record("gate", passed=False, error_type=type(error).__name__, grants_input_authority=False)
                raise

    def _owner_and_source(self, backend, source, command, started):
        owner, service = backend.owner, backend.owned_service
        identity = source.get("target_process_identity")
        binding = source.get("pointer_binding")
        if (self.display_proof(self.session) != self.display or service.process.poll() is not None
                or self.session.name != service.startup.get("display")
                or owner.owner_id != service.startup.get("owner_id")
                or owner.service_id != service.service_id or owner.obligation_snapshot() is not None):
            raise ValueError("owned input service identity or release obligation unverified")
        if (type(identity) is not dict or type(binding) is not dict
                or type(source.get("sequence")) is not int or type(command.get("expected_sequence")) is not int
                or command["expected_sequence"] != source["sequence"]
                or source["sequence"] != backend.sequence
                or type(identity.get("sequence")) is not int or identity["sequence"] != source["sequence"]
                or type(identity.get("surface")) is not int or identity["surface"] != binding.get("surface")
                or backend._source_identity != (source["sequence"], binding.get("surface"), identity.get("digest"))
                or type(source.get("input_owner_generation")) is not int
                or source["input_owner_generation"] != backend._owner_generation
                or type(source.get("capture_ns")) is not int
                or not 0 <= started - source["capture_ns"] < GATE_MAX_AGE_NS):
            raise ValueError("fresh source owner binding required")
        self._active_neutral()
        state = owner.call("input_state")
        now = self.clock()
        if (type(state) is not dict or state.get("owner_id") != owner.owner_id
                or state.get("owned_keycodes") != [] or state.get("owned_buttons") != []
                or state.get("release_pending") is not False or state.get("cancel_requested") is not False
                or "active_lease_deadline_ns" not in state or state["active_lease_deadline_ns"] is not None
                or type(state.get("physical_pointer_mask")) is not int or state["physical_pointer_mask"] != 0
                or type(state.get("focus")) is not int or state["focus"] != binding.get("focus")
                or type(state.get("sample_started_ns")) is not int
                or type(state.get("sample_finished_ns")) is not int
                or not started <= state["sample_started_ns"] <= state["sample_finished_ns"] <= now
                or now - started >= FIRST_PRESS_WINDOW_NS or service.process.poll() is not None
                or owner.obligation_snapshot() is not None):
            raise ValueError("fresh neutral input owner state required")
        return owner.owner_id, backend._owner_generation, state

    def check_submit(self, command, backend, source, *, terminal, accepted):
        if self.first_press_observed:
            return None
        identifier = command["id"]
        steps = command["steps"]
        if type(steps) is not list or not steps or any(type(step) is not dict or
                step.get("op") not in PASSIVE_STEPS | {"hold"} for step in steps):
            raise ValueError("startup gate supports passive observations and keyboard holds only")
        operations = {step["op"] for step in steps}
        initial = identifier == "cover-0"
        if not self.initial_cover_accepted and not initial and operations == {"observe"}:
            return None
        if not initial and self.initial_cover_accepted and operations <= PASSIVE_STEPS:
            return None
        if (initial and (self.initial_cover_accepted or operations != {"coast"})
                or not initial and not self.initial_cover_accepted):
            raise ValueError("verified initial passive cover required before input")
        started = self.clock()
        if initial and (self.validated_ns is None
                        or not 0 <= started - self.validated_ns < GATE_MAX_AGE_NS):
            raise ValueError("stale post-load clock proof before initial cover")
        owner, generation, state = self._owner_and_source(backend, source, command, started)
        if initial:
            if self.clock() - self.validated_ns >= GATE_MAX_AGE_NS:
                raise ValueError("stale post-load clock proof before initial cover")
            deadline = self.validated_ns + GATE_MAX_AGE_NS
        else:
            release = terminal.get("release") if type(terminal) is dict else None
            if (type(release) is not dict or terminal.get("status") not in ("completed", "expired", "cancelled")
                    or terminal.get("input_owner_id") != owner
                    or type(terminal.get("input_owner_generation")) is not int
                    or terminal["input_owner_generation"] != generation
                    or type(accepted) is not dict or terminal.get("id") != accepted.get("id")
                    or type(accepted.get("intent_token")) is not str or not accepted["intent_token"]
                    or release.get("event") != "owner_release" or release.get("verified") is not True
                    or release.get("intent_token") not in (None, accepted["intent_token"])
                    or any(release.get(field) != [] for field in
                           ("keys_down", "buttons_down", "keys_unknown", "key_state_errors"))):
                raise ValueError("latest passive cover release and owner proof required")
            deadline = started + FIRST_PRESS_WINDOW_NS
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"event": "submission_gate", "id": identifier,
                                     "observed_ns": self.clock(), "owner_id": owner,
                                     "owner_generation": generation, "owner_state": state,
                                     "source_sequence": source["sequence"], "terminal_id":
                                         terminal.get("id") if type(terminal) is dict else None,
                                     "admission_deadline_ns": deadline,
                                     "grants_input_authority": False}, allow_nan=False) + "\n")
        if initial:
            self.initial_cover_pending = True
        else:
            self.first_press = (identifier, owner, deadline)
            self.first_press_intent = None
        return deadline

    def record(self, event):
        if event.get("event") == "accepted":
            if event.get("id") == "cover-0" and self.initial_cover_pending:
                self.initial_cover_accepted = True
            if self.first_press is not None and event.get("id") == self.first_press[0]:
                token = event.get("intent_token")
                if type(token) is not str or not token:
                    raise RuntimeError("first input lease identity unverified")
                self.first_press_intent = token
        if event.get("event") == "input_admission" and not self.first_press_observed:
            if self.first_press is None:
                raise RuntimeError("input admission arrived before startup proof")
            identifier, owner, deadline = self.first_press
            if (event.get("id") != identifier or event.get("owner_id") != owner
                    or self.first_press_intent is None or event.get("intent_token") != self.first_press_intent
                    or type(event.get("first_press_deadline_ns")) is not int
                    or not 0 < event["first_press_deadline_ns"] <= deadline
                    or event.get("first_press_submission_checked_before_deadline") is not True
                    or type(event.get("admitted_ns")) is not int or type(event.get("input_ack_ns")) is not int
                    or not event["admitted_ns"] <= event["input_ack_ns"] < event["first_press_deadline_ns"]):
                raise RuntimeError("first key admission proof unverified")
            self.first_press_observed = True
