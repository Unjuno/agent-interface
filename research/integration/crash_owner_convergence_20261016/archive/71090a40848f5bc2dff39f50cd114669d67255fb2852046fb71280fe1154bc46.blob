"""Best-effort owned cleanup preserving the controller's primary failure."""
import atexit,hashlib,json,os,select,threading,time
from pathlib import Path

from input_owner_process_v1 import _write_receipt, read_recovery_receipt

_OWNER_KEYS = {"Left", "Right", "Up", "Down", "a", "d", "e", "space", "Shift_L"}


def read_owner_state_ledger(runtime, events):
    """Validate the owner-authored fsync ledger and return possibly held inputs."""
    ready = []
    for row in events:
        if type(row) is not dict:
            continue
        payload = row.get("event") if type(row.get("event")) is dict else row
        if payload.get("event") == "input_owner_process_ready":
            ready.append(payload)
    if len(ready) != 1:
        raise RuntimeError("expected exactly one process-owner ready event")
    identity = ready[0]
    path = Path(runtime) / "input-owner-process" / "input-owner-state-v1.jsonl"
    expected_receipt = Path(runtime) / "input-owner-process" / "input-owner-recovery-v1.json"
    if Path(identity.get("receipt_path", "")).resolve() != expected_receipt.resolve():
        raise RuntimeError("process-owner receipt path is outside session runtime")
    if (identity.get("schema") != "input-owner-process-ready-v1" or
            type(identity.get("service_pid")) is not int or
            identity["service_pid"] <= 1 or not isinstance(identity.get("owner_id"), str) or
            not identity["owner_id"] or not isinstance(identity.get("display"), str) or
            type(identity.get("service_start_ticks")) is not int):
        raise ValueError("process-owner ready identity is malformed")
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    if not rows or any(type(row) is not dict for row in rows):
        raise ValueError("owner state ledger must contain JSON objects")
    header = rows[0]
    if (header.get("schema") != "input-owner-state-ledger-v1" or
            header.get("record_type") != "header" or
            header.get("display") != identity.get("display") or
            header.get("service_pid") != identity.get("service_pid") or
            header.get("owner_id") != identity.get("owner_id") or
            header.get("service_start_ticks") != identity.get("service_start_ticks") or
            type(header.get("service_start_ticks")) is not int):
        raise ValueError("owner state ledger identity mismatch")
    active_keys = {}
    active_buttons = {}
    last_sequence = 0
    for row in rows[1:]:
        if (row.get("schema") != "input-owner-state-ledger-v1" or
                row.get("record_type") != "transition" or
                row.get("display") != header["display"] or
                row.get("service_pid") != header["service_pid"] or
                row.get("service_start_ticks") != header["service_start_ticks"] or
                row.get("owner_id") != header["owner_id"]):
            raise ValueError("owner state ledger transition identity mismatch")
        sequence = row.get("sequence")
        if type(sequence) is not int or sequence != last_sequence + 1:
            raise ValueError("owner state ledger sequence is not contiguous")
        last_sequence = sequence
        operation, phase, key = row.get("operation"), row.get("phase"), row.get("key")
        if phase not in {"intent", "ack", "error"}:
            raise ValueError("owner state ledger phase is invalid")
        if (type(row.get("request_id")) is not int and row.get("request_id") is not None):
            raise ValueError("owner state ledger request identity is invalid")
        if (row.get("intent_token") is not None and
                (not isinstance(row["intent_token"], str) or not row["intent_token"])):
            raise ValueError("owner state ledger intent token is invalid")
        if operation in {"down", "up"}:
            if not isinstance(key, str) or key not in _OWNER_KEYS:
                raise ValueError("owner state ledger key is not allowlisted")
            if operation == "down" and phase in {"intent", "ack"}:
                if type(row.get("expected_focus")) is not int or row["expected_focus"] <= 1:
                    raise ValueError("keyboard ledger entry lacks focus identity")
                active_keys[key] = dict(row)
            elif operation == "up" and phase == "ack":
                result = row.get("result")
                if type(result) is dict and result.get("verified") is True:
                    active_keys.pop(key, None)
        elif operation == "up_batch":
            if (type(key) is not list or not key or
                    any(not isinstance(k, str) or k not in _OWNER_KEYS for k in key) or
                    len(key) != len(set(key))):
                raise ValueError("owner state ledger up_batch keys are invalid")
            if phase == "ack":
                result = row.get("result")
                if type(result) is dict and result.get("verified") is True:
                    for item in key:
                        active_keys.pop(item, None)
        elif operation in {"button_down", "button_up"}:
            if type(key) is not int or key not in (1, 2, 3):
                raise ValueError("owner state ledger button is invalid")
            if operation == "button_down" and phase in {"intent", "ack"}:
                if (type(row.get("expected_focus")) is not int or
                        type(row.get("expected_surface")) is not int or
                        type(row.get("expected_geometry")) is not list):
                    raise ValueError("button ledger entry lacks focus/surface binding")
                active_buttons[key] = dict(row)
        elif operation == "release" and phase == "ack":
            result = row.get("result")
            if (type(result) is dict and result.get("verified") is True and
                    result.get("keys_down") == [] and result.get("buttons_down") == []):
                active_keys.clear(); active_buttons.clear()
        elif operation in {"close", "rpc_eof_close"} and phase == "ack":
            result = row.get("result")
            if type(result) is dict and result.get("release_verified") is True:
                active_keys.clear(); active_buttons.clear()
        elif operation not in {"move", "wheel", "surface_context", "continue_move",
                               "close", "rpc_eof_close", "release"}:
            raise ValueError("owner state ledger operation is unsupported")
    return {"path": path, "header": header, "rows": rows,
            "active_keys": active_keys, "active_buttons": active_buttons,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def _service_process_is_gone(identity, kill=os.kill):
    pid = identity["service_pid"]
    start_ticks = identity["service_start_ticks"]
    try:
        kill(pid, 0)
    except ProcessLookupError:
        return True
    except PermissionError as exc:
        raise RuntimeError("cannot verify owner service process permissions") from exc
    try:
        stat = Path(f"/proc/{pid}/stat").read_text(encoding="ascii")
    except FileNotFoundError:
        return True
    fields = stat[stat.rfind(")") + 2:].split()
    if len(fields) <= 19 or not fields[19].isdecimal():
        raise RuntimeError("cannot verify owner service process identity")
    current_start_ticks = int(fields[19])
    if current_start_ticks != start_ticks:
        return True
    return bool(fields[0] == "Z")


def recover_dead_owner_inputs(runtime, events, *, kill=os.kill, display_factory=None,
                              clock_ns=time.perf_counter_ns, sleep=time.sleep,
                              timeout=1.0, observer_connection=None):
    """Release only ledgered keys/buttons after verified owner death and focus match."""
    state = read_owner_state_ledger(runtime, events)
    header = state["header"]
    if not _service_process_is_gone(header, kill=kill):
        raise RuntimeError("input-owner service is still alive; emergency release refused")
    active_keys = state["active_keys"]
    active_buttons = state["active_buttons"]
    if not active_keys and not active_buttons:
        raise RuntimeError("owner state ledger contains no unresolved inputs")
    bindings = list(active_keys.values()) + list(active_buttons.values())
    focuses = {row.get("expected_focus") for row in bindings}
    if len(focuses) != 1 or None in focuses:
        raise RuntimeError("active owner inputs do not share one focus binding")
    expected_focus = focuses.pop()
    surfaces = {row.get("expected_surface") for row in active_buttons.values()}
    geometries = {tuple(row.get("expected_geometry") or ()) for row in active_buttons.values()}
    if len(surfaces) > 1 or len(geometries) > 1:
        raise RuntimeError("active owner buttons do not share one surface binding")
    expected_surface = next(iter(surfaces), None)
    expected_geometry = next(iter(geometries), None)
    receipt_path = Path(runtime) / "input-owner-process" / "input-owner-emergency-recovery-v1.json"
    if receipt_path.exists():
        raise FileExistsError("emergency recovery receipt already exists")

    if display_factory is None:
        from Xlib import X, XK, display
        from Xlib.ext import xtest
        display_factory = display.Display
    else:
        from Xlib import X, XK
        from Xlib.ext import xtest
    release_display = display_factory(header["display"])
    observer = (observer_connection if observer_connection is not None
                else display_factory(header["display"]))
    owns_observer = observer_connection is None
    try:
        if observer.get_display_name() != header["display"]:
            raise RuntimeError("recovery observer is connected to a different X display")
        focus = release_display.get_input_focus().focus
        focus_id = focus.id if hasattr(focus, "id") else focus
        if focus_id != expected_focus:
            raise RuntimeError("current X11 focus differs from ledgered owner focus")
        observed_focus = observer.get_input_focus().focus
        observed_focus_id = observed_focus.id if hasattr(observed_focus, "id") else observed_focus
        if observed_focus_id != expected_focus:
            raise RuntimeError("recovery observer focus differs from ledgered owner focus")
        root = release_display.screen().root
        if active_buttons:
            if type(expected_surface) is not int or expected_surface <= 1 or len(expected_geometry) != 4:
                raise RuntimeError("active button ledger lacks surface geometry")
            prop = root.get_full_property(release_display.intern_atom("_NET_ACTIVE_WINDOW"), X.AnyPropertyType)
            if prop is None or not len(prop.value) or int(prop.value[0]) != expected_surface:
                raise RuntimeError("active X11 surface differs from ledgered owner surface")
            surface = release_display.create_resource_object("window", expected_surface)
            geometry = surface.get_geometry()
            position = root.translate_coords(surface, 0, 0)
            actual_geometry = (position.x, position.y, geometry.width, geometry.height)
            if actual_geometry != tuple(expected_geometry):
                raise RuntimeError("active X11 surface geometry differs from owner ledger")
            pointer = root.query_pointer()
            x, y = pointer.root_x, pointer.root_y
            gx, gy, width, height = actual_geometry
            if not (gx <= x < gx + width and gy <= y < gy + height):
                raise RuntimeError("pointer is outside the ledgered active surface")
        if observer_connection is None:
            if active_buttons and expected_surface == expected_focus:
                observer.create_resource_object("window", expected_focus).change_attributes(
                    event_mask=X.KeyReleaseMask | X.ButtonReleaseMask)
            else:
                observer.create_resource_object("window", expected_focus).change_attributes(
                    event_mask=X.KeyReleaseMask)
            if active_buttons and expected_surface != expected_focus:
                observer.create_resource_object("window", expected_surface).change_attributes(
                    event_mask=X.ButtonReleaseMask)
            if active_buttons:
                observer.screen().root.change_attributes(event_mask=X.ButtonReleaseMask)
        observer.sync()
        keycodes = {}
        for key in sorted(active_keys):
            keysym = XK.string_to_keysym(key)
            code = release_display.keysym_to_keycode(keysym)
            if not code:
                raise RuntimeError("owner ledger key has no keycode on bound display")
            keycodes[key] = code
        before_bitmap = observer.query_keymap()
        before_keys = {key: bool(before_bitmap[code // 8] & (1 << (code % 8)))
                       for key, code in keycodes.items()}
        before_buttons = root.query_pointer().mask
        button_masks = {button: bool(before_buttons & (X.Button1Mask << (button - 1)))
                        for button in active_buttons}
        started_ns = clock_ns()
        for key, code in keycodes.items():
            if before_keys[key]:
                xtest.fake_input(release_display, X.KeyRelease, code)
        for button, down in button_masks.items():
            if down:
                xtest.fake_input(release_display, X.ButtonRelease, button)
        release_display.sync()
        sync_ns = clock_ns()
        deadline = time.monotonic() + timeout
        key_events = set(); button_events = set()
        while time.monotonic() < deadline:
            while observer.pending_events():
                event = observer.next_event()
                if event.type == X.KeyRelease and event.detail in keycodes.values():
                    key_events.add(event.detail)
                elif event.type == X.ButtonRelease and event.detail in active_buttons:
                    button_events.add(event.detail)
            bitmap = observer.query_keymap()
            after_keys = {key: bool(bitmap[code // 8] & (1 << (code % 8)))
                          for key, code in keycodes.items()}
            after_buttons_mask = observer.screen().root.query_pointer().mask
            after_buttons = {button: bool(after_buttons_mask & (X.Button1Mask << (button - 1)))
                             for button in active_buttons}
            if not any(after_keys.values()) and not any(after_buttons.values()):
                break
            sleep(.01)
        verified = (not any(after_keys.values()) and not any(after_buttons.values()) and
                    all(not before_keys[key] or code in key_events
                        for key, code in keycodes.items()) and
                    all(not button_masks[button] or button in button_events
                        for button in active_buttons))
        receipt = {"schema": "input-owner-emergency-recovery-v1",
                   "recovery_mode": "supervisor_xtest_after_owner_process_death",
                   "display": header["display"], "service_pid": header["service_pid"],
                   "service_start_ticks": header["service_start_ticks"],
                   "owner_id": header["owner_id"], "focus_id": expected_focus,
                   "surface_id": expected_surface, "surface_geometry": expected_geometry,
                   "ledger_path": str(state["path"]), "ledger_sha256": state["sha256"],
                   "active_keys": {key: {"keycode": keycodes[key], "was_down": before_keys[key],
                                         "release_event_observed": keycodes[key] in key_events,
                                         "up_verified": not after_keys[key]}
                                   for key in keycodes},
                   "active_buttons": {str(button): {"was_down": button_masks[button],
                                                     "release_event_observed": button in button_events,
                                                     "up_verified": not after_buttons[button]}
                                       for button in active_buttons},
                   "release_started_ns": started_ns, "sync_returned_ns": sync_ns,
                   "recovery_verified": verified, "receipt_fsynced": True,
                   "diagnostics": {"before_keys": before_keys, "before_buttons": button_masks,
                                   "release_keycodes_observed": sorted(key_events),
                                   "release_buttons_observed": sorted(button_events),
                                   "after_keys": after_keys, "after_buttons": after_buttons}}
        if receipt_path.exists():
            raise FileExistsError("emergency recovery receipt already exists")
        _write_receipt(receipt_path, receipt)
        if not verified:
            raise RuntimeError("supervisor emergency release was not independently verified; unverified receipt retained")
        return receipt
    finally:
        release_display.close()
        if owns_observer:
            observer.close()

def send_failure_finish(stream, timeout=0.25):
    """Attempt finish on an owned POSIX pipe without an unbounded flush.

    This failure-only path cannot certify protocol delivery or input release.
    Unsupported descriptors fail rather than falling back to a blocking write.
    The caller must have exclusive ownership of the stream during teardown.
    """
    if os.name != 'posix':
        raise NotImplementedError('bounded failure finish requires POSIX pipe')
    fd=stream.fileno()
    blocking=os.get_blocking(fd)
    deadline=time.monotonic()+timeout
    data=b'{"op":"finish"}\n'
    os.set_blocking(fd,False)
    try:
        while data:
            remaining=deadline-time.monotonic()
            if remaining <= 0: raise TimeoutError('failure finish pipe deadline')
            if not select.select([], [fd], [], remaining)[1]:
                raise TimeoutError('failure finish pipe deadline')
            try: written=os.write(fd,data)
            except BlockingIOError: continue
            if written <= 0: raise BrokenPipeError('failure finish made no progress')
            data=data[written:]
    finally:
        os.set_blocking(fd,blocking)


def verify_owner_process_recovery(runtime, events, *, timeout=8.0,
                                  clock=time.monotonic, sleep=time.sleep,
                                  kill=os.kill):
    """Require the session-published owner identity and durable close receipt."""
    ready = []
    for row in events:
        if type(row) is not dict:
            continue
        payload = row.get("event") if type(row.get("event")) is dict else row
        if payload.get("event") == "input_owner_process_ready":
            ready.append(payload)
    if len(ready) != 1:
        raise RuntimeError("expected exactly one process-owner ready event")
    row = ready[0]
    if (row.get("schema") != "input-owner-process-ready-v1" or
            not isinstance(row.get("owner_id"), str) or not row["owner_id"] or
            type(row.get("service_pid")) is not int or row["service_pid"] <= 1 or
            type(row.get("service_start_ticks")) is not int or
            not isinstance(row.get("display"), str) or not row["display"]):
        raise RuntimeError("process-owner ready identity is malformed")
    expected = (Path(runtime) / "input-owner-process" /
                "input-owner-recovery-v1.json").resolve()
    supplied = Path(row.get("receipt_path", "")).resolve()
    if supplied != expected:
        raise RuntimeError("process-owner receipt path is outside session runtime")
    deadline = clock() + timeout
    receipt = None
    while clock() < deadline:
        try:
            receipt = read_recovery_receipt(supplied, expected_display=row["display"])
        except (FileNotFoundError, json.JSONDecodeError, ValueError, RuntimeError):
            receipt = None
        service_exited = _service_process_is_gone(row, kill=kill)
        if (receipt is not None and service_exited and
                receipt.get("service_pid") == row["service_pid"] and
                receipt.get("service_start_ticks") == row["service_start_ticks"] and
                receipt.get("owner_id") == row["owner_id"]):
            return receipt
        if service_exited:
            raise TimeoutError("owner process exited without a matching verified receipt")
        sleep(min(.05, max(0, deadline - clock())))
    raise TimeoutError("verified process-owner receipt and service exit not observed")


def verify_or_recover_owner_process(runtime, events, *, timeout=8.0,
                                    clock=time.monotonic, sleep=time.sleep,
                                    kill=os.kill):
    """Prefer the owner receipt; use guarded emergency release only after timeout."""
    try:
        receipt = verify_owner_process_recovery(
            runtime, events, timeout=timeout, clock=clock, sleep=sleep, kill=kill)
        return {**receipt, "recovery_mode": "owner_process_verified_receipt"}
    except TimeoutError as receipt_error:
        try:
            receipt = recover_dead_owner_inputs(runtime, events, kill=kill)
            return receipt
        except BaseException as recovery_error:
            try:
                recovery_error.add_note(
                    "normal owner receipt was not observed: " + type(receipt_error).__name__)
            except BaseException:
                pass
            raise


class ControllerFailureCleanup:
    def __init__(self, planner, out, finish_timeout=0.5,
                 child_wait_timeout=5, escalation_wait_timeout=1,
                 owner_process_recovery=False):
        self.planner=planner;self.out=out;self.process=None
        self.finish_timeout=finish_timeout
        self.child_wait_timeout=child_wait_timeout
        self.escalation_wait_timeout=escalation_wait_timeout
        self.failed_stage='controller_setup'
        self.events=None;self.reader=None;self.event_wait=None;self.runtime=None
        self.reader_errors=[]
        self.owner_process_recovery=bool(owner_process_recovery)
    def track(self, process):
        self.process=process
    def set_stage(self, name):
        self.failed_stage=name
    def observe_output(self, events, reader, event_wait, runtime, reader_errors=None):
        self.events=events;self.reader=reader;self.event_wait=event_wait
        self.runtime=runtime
        self.reader_errors=[] if reader_errors is None else reader_errors
    def __enter__(self): return self
    def __exit__(self, kind, error, traceback):
        if error is None: return False
        receipt={'format':'controller-failure-cleanup-v1', 'primary_error_type':kind.__name__,
                 'failed_stage':self.failed_stage,'stages':[], 'input_release_verified':False,
                 'input_releases_verified_empty':False,
                 'scope':'owned child process only; no physical release or scorer certificate'}
        receipt['owner_process_recovery_required']=self.owner_process_recovery
        receipt['owner_process_recovery_verified']=False
        receipt['owner_process_emergency_recovery_verified']=False
        receipt['display_reuse_allowed']=not self.owner_process_recovery
        def attempt(name, operation):
            try:
                result=operation()
                receipt['stages'].append({'stage':name,'status':'returned','result':result})
                return True
            except BaseException as secondary:
                receipt['stages'].append({'stage':name,'status':'failed','error_type':type(secondary).__name__})
                try: error.add_note(name+' cleanup failed: '+type(secondary).__name__)
                except BaseException: pass
                return False
        def bounded(name, operation, timeout):
            result=[];finished=threading.Event()
            def invoke():
                try:result.append((True,operation()))
                except BaseException as secondary:result.append((False,secondary))
                finally:finished.set()
            worker=threading.Thread(target=invoke,daemon=True,name='controller-cleanup-'+name)
            if not attempt(name+'_worker_start',worker.start):return False,None,None
            if not finished.wait(timeout):
                receipt['stages'].append({'stage':name,'status':'timed_out',
                                          'timeout_seconds':timeout})
                try:error.add_note(name+' cleanup timed out')
                except BaseException:pass
                return False,None,worker
            worker.join(timeout=.1)
            succeeded,value=result[0]
            if succeeded:
                receipt['stages'].append({'stage':name,'status':'returned','result':value})
                return True,value,worker
            receipt['stages'].append({'stage':name,'status':'failed',
                                      'error_type':type(value).__name__})
            try:error.add_note(name+' cleanup failed: '+type(value).__name__)
            except BaseException:pass
            return False,None,worker
        child=self.process
        if child is not None:
            polled=attempt('child_poll_before',child.poll)
            if not polled or receipt['stages'][-1]['result'] is None:
                finish_sent=attempt('finish_send',lambda:send_failure_finish(
                    child.stdin,timeout=self.finish_timeout))
                if finish_sent and self.event_wait is not None:
                    attempt('post_control_score_wait',lambda:self.event_wait(
                        lambda row: type(row) is dict and
                        row.get('event')=='post_control_score',10))
                if finish_sent:
                    if not attempt('child_wait',lambda:child.wait(timeout=self.child_wait_timeout)):
                        attempt('child_terminate',child.terminate)
                        if not attempt('terminated_wait',lambda:child.wait(timeout=self.escalation_wait_timeout)):
                            attempt('child_kill',child.kill)
                            attempt('killed_wait',lambda:child.wait(timeout=self.escalation_wait_timeout))
                else:
                    receipt['stages'].append({'stage':'child_wait','status':'skipped',
                                              'reason':'finish_send_failed'})
                    poll_ok=attempt('child_poll_after_finish_failure',child.poll)
                    if not poll_ok or receipt['stages'][-1]['result'] is None:
                        attempt('child_terminate',child.terminate)
                        if not attempt('terminated_wait',lambda:child.wait(timeout=self.escalation_wait_timeout)):
                            attempt('child_kill',child.kill)
                            attempt('killed_wait',lambda:child.wait(timeout=self.escalation_wait_timeout))
                if hasattr(child.stdin,'close'):
                    bounded('child_stdin_close',child.stdin.close,.5)
            if attempt('child_poll_after',child.poll):
                receipt['child_exit_code']=receipt['stages'][-1]['result']
        bounded('planner_close',lambda:self.planner.close(timeout=1),1)
        attempt('atexit_unregister',lambda:atexit.unregister(self.planner.close))
        receipt['stdout_reader_retired']=False
        if self.reader is not None:
            attempt('stdout_reader_join',lambda:self.reader.join(timeout=5))
            reader_alive=attempt('stdout_reader_alive',self.reader.is_alive)
            if reader_alive:
                receipt['stdout_reader_retired']=not receipt['stages'][-1]['result']
        receipt['stdout_reader_errors']=list(self.reader_errors)
        events=self.events if type(self.events) is list else []
        accepted_ids={row.get('id') for row in events if type(row) is dict and
                      row.get('event')=='accepted' and type(row.get('id')) is str}
        accepted_by_id={row.get('id'):row for row in events if type(row) is dict and
                        row.get('event')=='accepted' and type(row.get('id')) is str}
        terminal_by_id={row.get('id'):row for row in events if type(row) is dict and
                        row.get('event')=='terminal' and type(row.get('id')) is str}
        event_set_complete=(receipt['stdout_reader_retired'] and
                            not receipt['stdout_reader_errors'])
        receipt['input_terminals_complete']=(event_set_complete and
                                              accepted_ids.issubset(terminal_by_id))
        receipt['input_releases_verified_empty']=(
            receipt['input_terminals_complete'] and all(
                type(terminal_by_id[identifier].get('release')) is dict and
                terminal_by_id[identifier]['release'].get('verified') is True and
                terminal_by_id[identifier]['release'].get('keys_down')==[] and
                terminal_by_id[identifier]['release'].get('buttons_down')==[] and
                ('intent_token' not in terminal_by_id[identifier]['release'] or
                 (type(accepted_by_id[identifier].get('intent_token')) is str and
                  bool(accepted_by_id[identifier]['intent_token']) and
                  terminal_by_id[identifier]['release'].get('intent_token') ==
                  accepted_by_id[identifier]['intent_token']))
            for identifier in accepted_ids))
        receipt['input_release_verified_empty']=receipt['input_releases_verified_empty']
        receipt['scorer_terminal_observed']=any(
            type(row) is dict and row.get('event')=='post_control_score' for row in events)
        score_path=None if self.runtime is None else self.runtime/'score.json'
        owner_path=None if self.runtime is None else self.runtime/'owner-events.json'
        receipt['score_file_present']=False
        if score_path is not None and attempt('score_file_presence',score_path.is_file):
            receipt['score_file_present']=receipt['stages'][-1]['result'] is True
        receipt['owner_events_present']=False
        if owner_path is not None and attempt('owner_events_presence',owner_path.is_file):
            receipt['owner_events_present']=receipt['stages'][-1]['result'] is True
        receipt['owner_events_closed']=False
        if receipt['owner_events_present']:
            try:
                owner_rows=json.loads(owner_path.read_text(encoding='utf-8'))
                receipt['owner_events_closed']=(
                    type(owner_rows) is list and bool(owner_rows) and
                    owner_rows[-1].get('reason')=='close' and
                    all(type(row) is dict and row.get('verified') is True
                        for row in owner_rows))
            except BaseException as secondary:
                receipt['stages'].append({'stage':'owner_events_read','status':'failed',
                                          'error_type':type(secondary).__name__})
                try: error.add_note('owner_events_read cleanup failed: '+type(secondary).__name__)
                except BaseException: pass
        if self.owner_process_recovery:
            child_exit=receipt.get('child_exit_code') is not None
            if child_exit and type(events) is list and self.runtime is not None:
                try:
                    owner_receipt=verify_or_recover_owner_process(self.runtime,events)
                    receipt['owner_process_recovery_verified']=True
                    receipt['owner_process_emergency_recovery_verified']=(
                        owner_receipt.get("recovery_mode") ==
                        "supervisor_xtest_after_owner_process_death")
                    receipt['owner_recovery_receipt']=owner_receipt
                    receipt['display_reuse_allowed']=True
                except BaseException as secondary:
                    receipt['stages'].append({'stage':'owner_process_recovery','status':'failed',
                                              'error_type':type(secondary).__name__})
                    try:error.add_note('owner process recovery failed: '+type(secondary).__name__)
                    except BaseException:pass
        child_exit=receipt.get('child_exit_code') is not None
        planner_closed=any(row.get('stage')=='planner_close' and row.get('status')=='returned'
                           for row in receipt['stages'])
        receipt['cleanup_complete']=all((
            child_exit,planner_closed,receipt['stdout_reader_retired'],
            not receipt['stdout_reader_errors'],receipt['input_terminals_complete'],
            receipt['input_releases_verified_empty'],receipt['scorer_terminal_observed'],
            receipt['score_file_present'],receipt['owner_events_closed'],
            receipt['display_reuse_allowed'],
            all(row.get('status')=='returned' for row in receipt['stages'])))
        attempt('failure_receipt_write',lambda:(self.out/'controller-failure.json').write_text(json.dumps(receipt,indent=2)+'\n'))
        return False
