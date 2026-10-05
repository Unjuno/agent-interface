"""Research input owner v12: one X11 connection with explicit key-up receipts.

This is scheduler-dependent deadline enforcement, not hard real-time control.
No user callback, image work, file write or stdout write runs on this thread.
"""
import queue
import threading
import time
import uuid
from Xlib import X, XK, display, error
from Xlib.ext import xtest
from executor_v3 import Cancelled, DecisionRequired


class InputOwner:
    def __init__(self, display_name):
        self.requests = queue.Queue()
        self.owner_id = uuid.uuid4().hex
        self.records = []
        self.ready = threading.Event()
        self.error = None
        self.closed = False
        self.display_name = display_name
        self.stopped = threading.Event()
        self.stop_requested = threading.Event()
        self.thread = threading.Thread(target=self._thread_main, name='input-owner', daemon=True)
        self.thread.start()
        if not self.ready.wait(2):
            self.stop_requested.set()
            self.closed = True
            raise RuntimeError('input owner startup timed out; cleanup unverified')
        if self.error is not None:
            self.thread.join(timeout=2)
            raise self.error

    def _thread_main(self):
        try:
            self._run()
        except BaseException as exc:
            self.error = exc
            self.records.append(dict(event='owner_failed', error=repr(exc), verified=False))
        finally:
            self.ready.set()
            self.stopped.set()

    def call(self, operation, lease=None, key=None):
        if self.closed or self.stopped.is_set() or self.stop_requested.is_set():
            raise RuntimeError('input owner unavailable') from self.error
        done, reply = threading.Event(), []
        self.requests.put((operation, lease, key, done, reply))
        deadline = time.monotonic() + 2
        while not done.wait(.01):
            if self.stopped.is_set():
                raise RuntimeError('input owner stopped before reply') from self.error
            if time.monotonic() >= deadline:
                if lease is not None: lease.cancel.set()
                self.stop_requested.set()
                self.error = RuntimeError('input owner reply timed out; cleanup unverified')
                raise self.error
        ok, result = reply[0]
        if not ok: raise result
        return result

    def close(self):
        if not self.closed:
            try:
                if not self.stopped.is_set() and not self.stop_requested.is_set():
                    self.call('close')
            finally:
                self.closed = True
                self.stop_requested.set()
                self.thread.join(timeout=2)
                if self.thread.is_alive():
                    raise RuntimeError('input owner still alive; cleanup unverified')

    def _run(self):
        try:
            d = display.Display(self.display_name)
        except Exception as exc:
            self.error = exc
            self.ready.set()
            return
        held = {}
        touched = set()
        buttons = {}
        touched_buttons = set()
        active = None
        active_pointer = False
        revision = 0
        fault = None
        self.ready.set()

        def key_is_down(code):
            bitmap = d.query_keymap()
            return bool(bitmap[code // 8] & (1 << (code % 8)))

        def sample_key_down(code):
            try:
                return key_is_down(code), None, time.perf_counter_ns()
            except Exception as exc:
                return None, {"type": type(exc).__name__, "message": str(exc)[:200]}, time.perf_counter_ns()

        def release_key(code, *, max_attempts=3, force_first=False):
            attempts = []
            server_down, before_error, _ = sample_key_down(code)
            for attempt in range(1, max_attempts + 1):
                if server_down is False and not (force_first and attempt == 1):
                    break
                observed_down_before = server_down
                started_ns = time.perf_counter_ns()
                release_error = None
                try:
                    xtest.fake_input(d, X.KeyRelease, code)
                except Exception as exc:
                    release_error = {"type": type(exc).__name__, "message": str(exc)[:200]}
                sync_error = None
                try:
                    d.sync()
                except Exception as exc:
                    sync_error = {"type": type(exc).__name__, "message": str(exc)[:200]}
                sync_returned_ns = time.perf_counter_ns() if sync_error is None else None
                server_down, after_error, sampled_ns = sample_key_down(code)
                attempts.append({
                    "attempt": attempt,
                    "keyrelease_started_ns": started_ns,
                    "sync_returned_ns": sync_returned_ns,
                    "keymap_sampled_ns": sampled_ns,
                    "server_key_down_before": observed_down_before,
                    "server_key_down_after": server_down,
                    "keymap_before_error": before_error,
                    "keymap_after_error": after_error,
                    "keyrelease_error": release_error,
                    "sync_error": sync_error,
                })
                before_error = after_error
                if server_down is False:
                    break
            return attempts, server_down is False

        def release_keys_batch(lease, keys):
            nonlocal fault
            if (type(keys) is not list or not keys or
                    any(not isinstance(key, str) or not key for key in keys) or
                    len(set(keys)) != len(keys)):
                raise ValueError('unique non-empty key list required for up_batch')
            if active is not lease or lease is None:
                raise ValueError('up_batch requires the active input lease')
            codes = []
            for key in keys:
                code = d.keysym_to_keycode(XK.string_to_keysym(key))
                if not code or held.get(code) is not lease:
                    raise ValueError('up_batch key is unavailable or not owned')
                codes.append((key, code))

            # The pre-sample occurs before the ordered UP sequence. Send every
            # original explicit UP before sampling again; this preserves the
            # release-batch no-query-between-UPs contract.
            try:
                before_bitmap = d.query_keymap()
                before_error = None
            except Exception as exc:
                before_bitmap = None
                before_error = {"type": type(exc).__name__, "message": str(exc)[:200]}
            attempt_rows = {}
            for key, code in codes:
                started_ns = time.perf_counter_ns()
                release_error = None
                try:
                    xtest.fake_input(d, X.KeyRelease, code)
                except Exception as exc:
                    release_error = {"type": type(exc).__name__, "message": str(exc)[:200]}
                sync_error = None
                try:
                    d.sync()
                except Exception as exc:
                    sync_error = {"type": type(exc).__name__, "message": str(exc)[:200]}
                sync_ns = time.perf_counter_ns() if sync_error is None else None
                attempt_rows[code] = [{
                    'attempt': 1,
                    'keyrelease_started_ns': started_ns,
                    'sync_returned_ns': sync_ns,
                    'keymap_sampled_ns': None,
                    'server_key_down_before': (
                        bool(before_bitmap[code // 8] & (1 << (code % 8)))
                        if before_bitmap is not None else None),
                    'server_key_down_after': None,
                    'keymap_before_error': before_error,
                    'keymap_after_error': None,
                    'keyrelease_error': release_error,
                    'sync_error': sync_error,
                }]

            try:
                bitmap = d.query_keymap()
                sample_error = None
                sampled_ns = time.perf_counter_ns()
            except Exception as exc:
                bitmap = None
                sample_error = {"type": type(exc).__name__, "message": str(exc)[:200]}
                sampled_ns = time.perf_counter_ns()
            receipts = []
            for key, code in codes:
                attempts = attempt_rows[code]
                server_down = (
                    bool(bitmap[code // 8] & (1 << (code % 8)))
                    if bitmap is not None else None)
                attempts[0]['keymap_sampled_ns'] = sampled_ns
                attempts[0]['server_key_down_after'] = server_down
                attempts[0]['keymap_after_error'] = sample_error
                while server_down is True and len(attempts) < 3:
                    started_ns = time.perf_counter_ns()
                    release_error = None
                    try:
                        xtest.fake_input(d, X.KeyRelease, code)
                    except Exception as exc:
                        release_error = {"type": type(exc).__name__, "message": str(exc)[:200]}
                    sync_error = None
                    try:
                        d.sync()
                    except Exception as exc:
                        sync_error = {"type": type(exc).__name__, "message": str(exc)[:200]}
                    sync_ns = time.perf_counter_ns() if sync_error is None else None
                    try:
                        bitmap = d.query_keymap()
                        sample_error = None
                        sampled_ns = time.perf_counter_ns()
                    except Exception as exc:
                        bitmap = None
                        sample_error = {"type": type(exc).__name__, "message": str(exc)[:200]}
                        sampled_ns = time.perf_counter_ns()
                    server_down = (
                        bool(bitmap[code // 8] & (1 << (code % 8)))
                        if bitmap is not None else None)
                    attempts.append({
                        'attempt': len(attempts) + 1,
                        'keyrelease_started_ns': started_ns,
                        'sync_returned_ns': sync_ns,
                        'keymap_sampled_ns': sampled_ns,
                        'server_key_down_before': True,
                        'server_key_down_after': server_down,
                        'keymap_before_error': None,
                        'keymap_after_error': sample_error,
                        'keyrelease_error': release_error,
                        'sync_error': sync_error,
                    })
                    if server_down is None:
                        break
                verified = server_down is False
                if verified:
                    held.pop(code, None)
                receipt = dict(
                    event='owner_explicit_keyup', operation='up',
                    owner_id=self.owner_id, key=key, keycode=code,
                    intent_token=getattr(lease, 'intent_token', None),
                    valid_until_ns=getattr(lease, 'deadline', None),
                    owner_keyrelease_started_ns=attempts[0]['keyrelease_started_ns'],
                    owner_sync_returned_ns=attempts[-1]['sync_returned_ns'],
                    owner_keymap_sampled_ns=attempts[-1]['keymap_sampled_ns'],
                    server_keyup_verified=verified,
                    server_keyup_attempt_count=len(attempts),
                    server_keyup_attempts=attempts,
                    server_key_down_after_keyup=server_down,
                    key_state_source='x11_query_keymap',
                    cancel_requested_after_sync=lease.cancel.is_set(),
                    server_sync_completed=any(row['sync_error'] is None for row in attempts),
                    physical_verification_authoritative=False,
                    release_batch_initial_up_count=len(codes),
                    release_batch_key_order=[item[0] for item in codes])
                self.records.append(receipt)
                receipts.append(receipt)
            if any(not receipt["server_keyup_verified"] for receipt in receipts):
                fault = RuntimeError("input owner failed closed after unverified key-up")
            return receipts

        def focus_id():
            value=d.get_input_focus().focus
            return value.id if hasattr(value,'id') else value

        def invalid_focus(lease, pointer=False):
            if not hasattr(lease,'expected_focus'):
                raise ValueError('observed input focus required')
            actual=focus_id()
            if not pointer:return actual != lease.expected_focus
            surface=getattr(lease,'expected_surface',None)
            if surface in (None,0,1) or actual in (None,0,1) or lease.expected_focus in (None,0,1):return True
            if held and actual!=lease.expected_focus:return True
            root=d.screen().root
            prop=root.get_full_property(d.intern_atom('_NET_ACTIVE_WINDOW'),X.AnyPropertyType)
            if prop is None or not len(prop.value) or int(prop.value[0])!=surface:return True
            def inside(identifier):
                node=d.create_resource_object('window',identifier)
                try:
                    for _ in range(32):
                        if node.id==surface:return True
                        if node.id==root.id:return False
                        node=node.query_tree().parent
                except (error.BadWindow,error.BadDrawable):return False
                return False
            return not (inside(lease.expected_focus) and inside(actual))

        def surface_context(surface):
            if type(surface) is not int or surface in (0,1):
                raise ValueError('client surface ID required')
            w=d.create_resource_object('window',surface)
            try:
                g=w.get_geometry()
                pos=d.screen().root.translate_coords(w,0,0)
                if w.get_attributes().map_state != X.IsViewable:
                    raise DecisionRequired()
            except (error.BadWindow,error.BadDrawable):
                raise DecisionRequired()
            return [pos.x,pos.y,g.width,g.height]

        def geometry_matches(lease):
            expected=getattr(lease,'expected_geometry',None)
            if not isinstance(expected,(list,tuple)) or len(expected)!=4 or any(type(x) is not int for x in expected):
                raise ValueError('observed surface geometry required')
            try:
                return surface_context(lease.expected_surface)==list(expected)
            except DecisionRequired:
                return False

        def hit_surface(lease, x, y):
            # Surface ID must come from the observation, not the requested point.
            surface = getattr(lease, 'expected_surface', None)
            if type(surface) is not int or surface in (0, 1):
                raise ValueError('observed client surface required for pointer input')
            root = d.screen().root
            node = root
            for _ in range(32):
                try:
                    child = node.translate_coords(root, x, y).child
                except error.BadWindow:
                    return False
                if not child or not getattr(child, 'id', 0):
                    return False
                if child.id == surface:
                    return True
                node = child
            return False

        def pointer_guard(lease, x, y):
            if fault is not None:
                raise RuntimeError('input owner failed closed') from fault
            if active is not None and active is not lease:
                raise ValueError('another intent owns input')
            if getattr(lease, 'focus_invalid', False) or invalid_focus(lease,pointer=True):
                lease.focus_invalid = True
                raise DecisionRequired()
            if not geometry_matches(lease) or not hit_surface(lease, x, y):
                lease.focus_invalid = True
                raise DecisionRequired()
            lease.check()
            if lease.cancel.is_set():
                raise Cancelled()

        def release(reason):
            nonlocal active,revision,fault
            revision += 1
            key_release_attempts = {}
            key_state_errors = []
            # Include every key this owner touched, not only keys still present
            # in bookkeeping. A lost explicit up must remain recoverable here.
            release_codes = list(held)
            release_codes.extend(sorted(set(touched) - set(held)))
            for code in release_codes:
                attempts, verified = release_key(code)
                key_release_attempts[str(code)] = {
                    "attempts": attempts, "verified": verified,
                }
            # An explicit ButtonRelease may be acknowledged by XSync while
            # the server still reports the button down. Retry every touched
            # button that remains down, including one removed from `buttons`.
            try:
                before_mask = d.screen().root.query_pointer().mask
            except Exception as exc:
                key_state_errors.append({"source": "pointer_before", "type": type(exc).__name__, "message": str(exc)[:200]})
                retry_buttons = set(buttons) | set(touched_buttons)
            else:
                retry_buttons = {
                    button for button in touched_buttons
                    if before_mask & (X.Button1Mask << (button - 1))
                }
            for button in sorted(retry_buttons):
                try:
                    xtest.fake_input(d, X.ButtonRelease, button)
                except Exception as exc:
                    key_state_errors.append({"source": "button_release", "button": button,
                                             "type": type(exc).__name__, "message": str(exc)[:200]})
            try:
                d.sync()
            except Exception as exc:
                key_state_errors.append({"source": "button_release_sync", "type": type(exc).__name__,
                                         "message": str(exc)[:200]})
            try:
                mask = d.screen().root.query_pointer().mask
                buttons_down = [b for b in touched_buttons if mask & (X.Button1Mask << (b-1))]
            except Exception as exc:
                key_state_errors.append({"source": "pointer_after", "type": type(exc).__name__, "message": str(exc)[:200]})
                buttons_down = sorted(set(buttons) | set(touched_buttons))
            down = []
            unknown_keys = []
            for code in sorted(touched):
                sampled, sample_error, _ = sample_key_down(code)
                if sampled is True:
                    down.append(code)
                elif sampled is None:
                    unknown_keys.append(code)
                    key_state_errors.append({"source": "keymap_after", "keycode": code, **sample_error})
            if reason == 'release' and active is not None and active.cancel.is_set():
                reason = 'cancelled'
            record = dict(event='owner_release', reason=reason, verified=not down and not buttons_down and not unknown_keys and not key_state_errors, buttons_down=buttons_down,
                          keys_down=down, keys_unknown=unknown_keys, key_state_errors=key_state_errors, verified_ns=time.perf_counter_ns(),
                          valid_until_ns=active.deadline if active else None,
                          key_release_attempts=key_release_attempts,
                          key_release_intervals_ns=[
                              {"keycode": int(code), "interval_ns": [
                                  attempts[0]["keyrelease_started_ns"],
                                  attempts[-1]["keymap_sampled_ns"]]}
                              for code, value in key_release_attempts.items()
                              if (attempts := value["attempts"])
                          ],
                          key_state_source='x11_query_keymap')
            if active is not None and hasattr(active, 'record_interruption'):
                active.record_interruption(record)
            self.records.append(record)
            if down or buttons_down or unknown_keys or key_state_errors:
                error = RuntimeError('owner release not verified: ' + repr(down))
                error.owner_release_record = record
                fault = error
                raise error
            buttons.clear()
            touched_buttons.clear()
            held.clear()
            touched.clear()
            active = None
            fault = None
            return record

        try:
            while True:
                if self.stop_requested.is_set():
                    release('stop_requested')
                    break
                # Check before dequeue so a busy request queue cannot starve expiry.
                if active is not None:
                    expired = time.perf_counter_ns() >= active.deadline
                    changed=invalid_focus(active,pointer=active_pointer)
                    surface_changed=False
                    if buttons and not changed:
                        point=d.screen().root.query_pointer()
                        surface_changed=not geometry_matches(active) or not hit_surface(active,point.root_x,point.root_y)
                        changed=surface_changed
                    if changed:active.focus_invalid=True
                    if expired or active.cancel.is_set() or changed:
                        try:
                            release('expired' if expired else ('surface_changed' if surface_changed else ('focus_changed' if changed else 'cancelled')))
                        except Exception as exc:
                            fault = exc
                            active = None
                timeout = .002
                if active is not None:
                    timeout = min(timeout, max(0, (active.deadline-time.perf_counter_ns())/1e9))
                try:
                    op, lease, key, done, reply = self.requests.get(timeout=timeout)
                except queue.Empty:
                    continue
                closing = op == 'close'
                try:
                    continuation = op == 'continue_move'
                    if continuation:
                        if not isinstance(key,dict) or set(key)!={'owner_id','expected_revision','x','y','reply_until_ns'}:
                            raise ValueError('continuation identity, revision and point required')
                        if key['owner_id']!=self.owner_id or type(key['expected_revision']) is not int or key['expected_revision']!=revision:
                            raise ValueError('obsolete continuation owner/revision')
                        if active is not lease or len(buttons)!=1 or held:
                            raise ValueError('continuation requires this active pointer-only hold')
                        reply_deadline=key['reply_until_ns']
                        if type(reply_deadline) is not int or reply_deadline>lease.deadline:raise ValueError('reply deadline must fit original lease')
                        if time.perf_counter_ns()>=reply_deadline:raise DecisionRequired('continuation response expired')
                        point=d.screen().root.query_pointer()
                        if not all(point.mask & (X.Button1Mask << (b-1)) for b in buttons):
                            raise DecisionRequired('held button no longer physically down')
                        op='move';key={'x':key['x'],'y':key['y']}
                    if op in ('move','button_down','button_up','wheel','down','up','up_batch'):revision += 1
                    if op == 'input_state':
                        started=time.perf_counter_ns();point=d.screen().root.query_pointer();focus=focus_id();finished=time.perf_counter_ns()
                        result=dict(owner_id=self.owner_id,revision=revision,sample_started_ns=started,sample_finished_ns=finished,
                            owned_buttons=sorted(buttons),owned_keycodes=sorted(held),physical_pointer_mask=point.mask,
                            pointer=[point.root_x,point.root_y],focus=focus,
                            active_lease_deadline_ns=active.deadline if active else None,
                            active_lease_time_valid=active is not None and finished<active.deadline,
                            cancel_requested=active.cancel.is_set() if active else False)
                    elif op == 'surface_context':
                        result = surface_context(key)
                    elif op in ('release', 'close'):
                        if op == 'release' and active is not None and active is not lease:
                            raise ValueError('release belongs to another intent')
                        reason = ('cancelled' if op == 'release' and active is lease and lease is not None and lease.cancel.is_set() else op)
                        result = release(reason)
                    elif op in ('move', 'button_down', 'button_up', 'wheel'):
                        root = d.screen().root
                        if op == 'button_up':
                            if type(key) is not int or key not in (1,2,3):
                                raise ValueError('button must be 1..3')
                            if key in buttons and buttons[key] is not lease:
                                raise ValueError('button belongs to another intent')
                            if key in buttons:
                                xtest.fake_input(d, X.ButtonRelease, key)
                                d.sync()
                                del buttons[key]
                            result = None
                        else:
                            if op == 'move':
                                if not isinstance(key, dict) or set(key) != {'x','y'} or any(type(key[k]) is not int for k in ('x','y')):
                                    raise ValueError('integer absolute x/y required')
                                x,y = key['x'],key['y']
                                geo = root.get_geometry()
                                if not (0 <= x < geo.width and 0 <= y < geo.height):
                                    raise ValueError('point outside root')
                            else:
                                point = root.query_pointer()
                                x,y = point.root_x,point.root_y
                                if type(key) is not int or (op == 'button_down' and key not in (1,2,3)) or (op == 'wheel' and (key == 0 or abs(key)>10)):
                                    raise ValueError('invalid button or wheel count')
                            pointer_guard(lease,x,y)
                            if continuation and time.perf_counter_ns()>=reply_deadline:raise DecisionRequired('continuation response expired')
                            active = lease
                            active_pointer = True
                            admitted = time.perf_counter_ns()
                            if op == 'move':
                                xtest.fake_input(d,X.MotionNotify,x=x,y=y)
                            elif op == 'button_down':
                                if key in buttons:
                                    raise ValueError('button already held')
                                buttons[key] = lease
                                touched_buttons.add(key)
                                xtest.fake_input(d,X.ButtonPress,key)
                            else:
                                button = 4 if key > 0 else 5
                                for _ in range(abs(key)):
                                    pointer_guard(lease,x,y)
                                    xtest.fake_input(d,X.ButtonPress,button)
                                    xtest.fake_input(d,X.ButtonRelease,button)
                            d.sync()
                            result = dict(event='pointer_admission', operation=op, payload=key,
                                          admitted_ns=admitted,input_ack_ns=time.perf_counter_ns(),
                                          valid_until_ns=lease.deadline, surface=lease.expected_surface)
                    elif op == 'up_batch':
                        result = release_keys_batch(lease, key)
                    elif op in ('down', 'up'):
                        code = d.keysym_to_keycode(XK.string_to_keysym(key))
                        if not code:
                            raise ValueError('key unavailable on input owner')
                        if op == 'down':
                            if fault is not None:
                                raise RuntimeError('input owner failed closed') from fault
                            if active is not None and active is not lease:
                                raise ValueError('another intent owns input')
                            if getattr(lease,'focus_invalid',False) or invalid_focus(lease):
                                lease.focus_invalid=True
                                raise DecisionRequired()
                            lease.check()
                            if lease.cancel.is_set():
                                raise Cancelled()
                            admitted = time.perf_counter_ns()
                            active = lease
                            active_pointer = False
                            touched.add(code)
                            held[code] = lease
                            xtest.fake_input(d, X.KeyPress, code)
                            d.sync()
                            result = dict(event='input_admission', key=key, admitted_ns=admitted,
                                          input_ack_ns=time.perf_counter_ns(), valid_until_ns=lease.deadline)
                        else:
                            # Cleanup from an old intent must never release a newer hold.
                            if code in held and held[code] is not lease:
                                raise ValueError('key belongs to another intent')
                            if code in held:
                                key_release_attempts, server_keyup_verified = release_key(
                                    code, force_first=True)
                                owner_keyrelease_started_ns = key_release_attempts[0]["keyrelease_started_ns"]
                                owner_sync_returned_ns = key_release_attempts[-1]["sync_returned_ns"]
                                owner_keymap_sampled_ns = key_release_attempts[-1]["keymap_sampled_ns"]
                                cancel = getattr(lease, 'cancel', None)
                                cancel_requested_after_sync = (
                                    cancel.is_set() if callable(getattr(cancel, 'is_set', None))
                                    else None
                                )
                                receipt = dict(
                                    event='owner_explicit_keyup', operation='up',
                                    owner_id=self.owner_id, key=key, keycode=code,
                                    intent_token=getattr(lease, 'intent_token', None),
                                    valid_until_ns=getattr(lease, 'deadline', None),
                                    owner_keyrelease_started_ns=owner_keyrelease_started_ns,
                                    owner_sync_returned_ns=owner_sync_returned_ns,
                                    owner_keymap_sampled_ns=owner_keymap_sampled_ns,
                                    server_keyup_verified=server_keyup_verified,
                                    server_keyup_attempt_count=len(key_release_attempts),
                                    server_keyup_attempts=key_release_attempts,
                                    server_key_down_after_keyup=not server_keyup_verified,
                                    key_state_source='x11_query_keymap',
                                    cancel_requested_after_sync=cancel_requested_after_sync,
                                    server_sync_completed=any(
                                        row['sync_error'] is None for row in key_release_attempts
                                    ),
                                    physical_verification_authoritative=False)
                                self.records.append(receipt)
                                if not server_keyup_verified:
                                    error = RuntimeError(
                                        'explicit key-up not observed in X11 keymap: ' + str(code))
                                    error.owner_explicit_keyup_record = receipt
                                    raise error
                                del held[code]
                            result = None
                    else:
                        raise ValueError('unknown input operation')
                    if continuation and isinstance(result,dict):
                        result.update(continuation=True,owner_id=self.owner_id,revision=revision)
                    reply.append((True, result))
                except Exception as exc:
                    explicit_up = getattr(exc, "owner_explicit_keyup_record", None)
                    if isinstance(explicit_up, dict) and not explicit_up.get("server_keyup_verified"):
                        fault = exc
                    reply.append((False, exc))
                finally:
                    done.set()
                if closing:
                    break
        finally:
            try:
                if held or buttons: release('thread_exit')
            except BaseException as exc:
                self.records.append(dict(event='cleanup_failed', error=repr(exc), verified=False))
            finally:
                d.close()
