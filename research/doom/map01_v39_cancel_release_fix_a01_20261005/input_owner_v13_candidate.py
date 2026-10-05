"""Research InputOwner v13 candidate: add measured per-key cancellation cleanup edges.

This successor retains v12 control semantics and ordinary key-edge measurements.
Cancellation cleanup samples each owner-held key around its release, emits a
context-bound receipt when the physical edge is confirmed, and never grants
input authority.
"""
import queue
import threading
import time
import uuid
from Xlib import X, XK, display, error
from Xlib.ext import xtest
from executor_v3 import Cancelled, DecisionRequired


def _valid_identity_text(value):
    return type(value) is str and bool(value.strip())


def _classify_press(owner_owned_before, pre_key_down, press_attempted, sync_succeeded, post_key_down, owner_owned_after):
    if any(type(x) is not bool for x in (owner_owned_before, pre_key_down, press_attempted, sync_succeeded, post_key_down, owner_owned_after)):
        raise ValueError('invalid physical press evidence')
    if sync_succeeded and not press_attempted:
        raise ValueError('sync without press')
    if owner_owned_before:
        return 'OWNER_ALREADY_HELD', None
    if pre_key_down:
        return 'PREEXISTING_PHYSICAL_DOWN', None
    if press_attempted and sync_succeeded and post_key_down and owner_owned_after:
        return 'CONFIRMED_PHYSICAL_DOWN', None  # interval supplied by caller samples
    return 'PRESS_UNCONFIRMED', None


def _classify_release(owner_owned, pre_key_down, release_attempted, sync_succeeded, post_key_down):
    if any(type(x) is not bool for x in (owner_owned, pre_key_down, release_attempted, sync_succeeded, post_key_down)):
        raise ValueError('invalid physical release evidence')
    if sync_succeeded and not release_attempted:
        raise ValueError('sync without release')
    if release_attempted and not owner_owned:
        raise ValueError('release without ownership')
    if not owner_owned:
        return ('FOREIGN_OR_STALE_DOWN' if pre_key_down else 'NOOP_ALREADY_UP'), None
    if not pre_key_down:
        return 'OWNER_PHYSICAL_MISMATCH', None
    if release_attempted and sync_succeeded and not post_key_down:
        return 'CONFIRMED_PHYSICAL_UP', None  # interval supplied by caller samples
    return 'RELEASE_UNCONFIRMED', None


class _HoldIdentity:
    """Owner-local stable physical-hold generation; measurement evidence only."""
    def __init__(self, owner_id):
        self.owner_id=owner_id
        self.counter=0
        self.active={}  # keycode -> (intent_token, key_name, actuation_id, event_context)
        self.retired=set()

    def on_down(self, code, key, intent_token, owner_owned_before, confirmed_new_edge, event_context=None):
        cur=self.active.get(code)
        if cur is not None:
            cur_intent,cur_key,aid,_=cur
            if not _valid_identity_text(intent_token) or (cur_intent,cur_key)!=(intent_token,key):
                return 'LINEAGE_MISMATCH', None
            if owner_owned_before:
                return 'ACTIVE_REUSED', aid
            # Physical/local ownership continuity is unresolved. Do not remint or expose stale lineage.
            return 'ACTIVE_WITHOUT_OWNER_HOLD', None
        if owner_owned_before:
            return 'OWNER_HOLD_IDENTITY_MISSING', None
        if not confirmed_new_edge:
            return 'UNCONFIRMED_DOWN_NO_ID', None
        if not _valid_identity_text(intent_token):
            return 'LINEAGE_UNAVAILABLE', None
        self.counter += 1
        aid=f'{self.owner_id}:g{self.counter}:{key}'
        if aid in self.retired:
            raise RuntimeError('retired actuation identity reuse')
        self.active[code]=(intent_token,key,aid,event_context)
        return 'MINTED', aid

    def on_up(self, code, key, intent_token, confirmed_up_edge):
        if not confirmed_up_edge:
            return 'UNCONFIRMED_UP_NO_CHANGE', None
        cur=self.active.get(code)
        if cur is None:
            return 'NO_ACTIVE_ID', None
        cur_intent,cur_key,aid,_=cur
        if not _valid_identity_text(intent_token) or (cur_intent,cur_key)!=(intent_token,key):
            return 'LINEAGE_MISMATCH', None
        del self.active[code]
        self.retired.add(aid)
        return 'RETIRED', aid

    def terminate_after_verified_neutral(self):
        # Aggregate cleanup may end a known hold lineage, but is not a per-key fresh-edge receipt.
        for _,_,aid,_ in self.active.values():
            self.retired.add(aid)
        self.active.clear()


def _edge_for_adapter(edge, bracket, actuation_id):
    if bracket is None or not _valid_identity_text(actuation_id):
        return None
    interval=bracket['physical_down_interval'] if edge=='down' else bracket['physical_up_interval']
    return dict(edge=edge,status=bracket['status'],actuation_id=actuation_id,owner_id=bracket['owner_id'],
                intent_token=bracket['intent_token'],key=bracket['key'],interval=interval,
                grants_input_authority=False)


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

    def call(self, operation, lease=None, key=None, event_context=None):
        if self.closed or self.stopped.is_set() or self.stop_requested.is_set():
            raise RuntimeError('input owner unavailable') from self.error
        done, reply = threading.Event(), []
        if event_context is not None and (not isinstance(event_context, (tuple, list)) or len(event_context) != 2 or type(event_context[0]) is not str or not event_context[0] or type(event_context[1]) is not int or event_context[1] < 0):
            raise ValueError('invalid program/step input context')
        self.requests.put((operation, lease, key, event_context, done, reply))
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
        hold_identity = _HoldIdentity(self.owner_id)
        self.ready.set()

        def lease_intent_token(lease):
            token=getattr(lease,'intent_token',None)
            return token if _valid_identity_text(token) else None

        def sample_key_state(code):
            started=time.perf_counter_ns()
            try:
                bitmap=d.query_keymap()
                is_down=bool(bitmap[code // 8] & (1 << (code % 8)))
            except Exception as exc:
                return dict(available=False,down=None,started_ns=started,finished_ns=time.perf_counter_ns(),error=type(exc).__name__)
            return dict(available=True,down=is_down,started_ns=started,finished_ns=time.perf_counter_ns(),error=None)

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
            per_key_release_measurements=[]
            def release_edges():
                for code in list(held):
                    key_lease=held[code]
                    identity=hold_identity.active.get(code)
                    pre=sample_key_state(code)
                    release_request_ns=time.perf_counter_ns()
                    xtest.fake_input(d, X.KeyRelease, code)
                    d.sync()
                    sync_return_ns=time.perf_counter_ns()
                    post=sample_key_state(code)
                    if identity is not None:
                        intent_token,key_name,actuation_id,event_context=identity
                    else:
                        intent_token=lease_intent_token(key_lease)
                        key_name=None;actuation_id=None;event_context=None
                    classification='PHYSICAL_SAMPLE_UNAVAILABLE'
                    physical_interval=None
                    if pre['available'] and post['available']:
                        classification,_=_classify_release(True,pre['down'],True,True,post['down'])
                        if classification=='CONFIRMED_PHYSICAL_UP':
                            physical_interval=[pre['finished_ns'],post['finished_ns']]
                    if classification == 'CONFIRMED_PHYSICAL_UP':
                        # The owner-held map tracks this owner's current physical
                        # hold. Retire it at the confirmed per-key edge, even when
                        # the later aggregate device queries fail.
                        held.pop(code, None)
                    identity_status,retired_id=hold_identity.on_up(
                        code,key_name,intent_token,classification=='CONFIRMED_PHYSICAL_UP') if key_name is not None else ('NO_ACTIVE_ID',None)
                    if retired_id is not None:
                        actuation_id=retired_id
                    bracket=None
                    if physical_interval is not None and actuation_id is not None and event_context is not None:
                        bracket=dict(status=classification,physical_up_interval=physical_interval,
                                     release_id=f'{self.owner_id}:r{revision}:cleanup-up:{code}',
                                     owner_id=self.owner_id,intent_token=intent_token,key=key_name,
                                     grants_input_authority=False,application_consumption_observed=False)
                    measurement=dict(edge='up',classification=classification,bracket=bracket,
                        actuation_id=actuation_id,identity_status=identity_status,
                        pre_sample=pre,post_sample=post,release_attempted=True,
                        release_request_ns=release_request_ns,sync_return_ns=sync_return_ns,
                        adapter_edge=_edge_for_adapter('up',bracket,actuation_id),
                        grants_input_authority=False,application_consumption_observed=False)
                    if actuation_id is not None and event_context is not None:
                        per_key_release_measurements.append(dict(
                            event='input_release_measurement',key=key_name,
                            id=event_context[0],step=event_context[1],owner_id=self.owner_id,
                            intent_token=intent_token,reason=reason,
                            physical_key_measurement=measurement,grants_input_authority=False))
                for button in list(buttons):
                    xtest.fake_input(d, X.ButtonRelease, button)
                d.sync()
            try:
                release_edges()
            except BaseException as exc:
                # Preserve completed per-key rows if a later edge or sync fails.
                # This partial record is appended once and never mutated.
                self.records.append(dict(
                    event='owner_release', reason=reason, verified=False,
                    valid_until_ns=active.deadline if active else None,
                    per_key_release_measurements=list(per_key_release_measurements)))
                fault=exc
                active=None
                raise
            # Persist per-key release evidence before aggregate reconciliation. The
            # physical key-up may be confirmed even if either global state query
            # fails; retain that row without marking the whole input state verified.
            record = dict(event='owner_release', reason=reason, verified=False,
                          valid_until_ns=active.deadline if active else None,
                          per_key_release_measurements=per_key_release_measurements)
            self.records.append(record)
            try:
                mask = d.screen().root.query_pointer().mask
                buttons_down = [b for b in touched_buttons if mask & (X.Button1Mask << (b-1))]
                bitmap = d.query_keymap()
                down = [code for code in touched if bitmap[code // 8] & (1 << (code % 8))]
            except Exception as exc:
                # Keep the partial receipt, preserve the aggregate error, and
                # stop accepting work from this owner after verification fails.
                fault = exc
                active = None
                raise
            record.update(verified=not down and not buttons_down, buttons_down=buttons_down,
                          keys_down=down, verified_ns=time.perf_counter_ns())
            if active is not None and hasattr(active, 'record_interruption'):
                active.record_interruption(record)
            if down or buttons_down:
                raise RuntimeError('owner release not verified: ' + repr(down))
            hold_identity.terminate_after_verified_neutral()
            buttons.clear()
            touched_buttons.clear()
            held.clear()
            touched.clear()
            active = None
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
                    op, lease, key, event_context, done, reply = self.requests.get(timeout=timeout)
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
                    if op in ('move','button_down','button_up','wheel','down','up'):revision += 1
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
                        reason = ('expired' if op == 'release' and active is not None
                                  and time.perf_counter_ns() >= active.deadline else op)
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
                            owner_owned_before = code in held
                            pre = sample_key_state(code)
                            active = lease
                            active_pointer = False
                            touched.add(code)
                            held[code] = lease
                            press_request_ns=time.perf_counter_ns()
                            xtest.fake_input(d, X.KeyPress, code)
                            d.sync()
                            sync_return_ns=time.perf_counter_ns()
                            input_ack_ns=sync_return_ns
                            post = sample_key_state(code)
                            intent_token=lease_intent_token(lease)
                            bracket=None; classified_status='PHYSICAL_SAMPLE_UNAVAILABLE'; physical_interval=None
                            if pre['available'] and post['available']:
                                classified_status,_=_classify_press(owner_owned_before,pre['down'],True,True,post['down'],code in held and held[code] is lease)
                                physical_interval=[pre['finished_ns'],post['finished_ns']] if classified_status=='CONFIRMED_PHYSICAL_DOWN' else None
                                if intent_token is not None:
                                    bracket=dict(status=classified_status,physical_down_interval=physical_interval,
                                                 press_id=f'{self.owner_id}:r{revision}:down:{code}',owner_id=self.owner_id,
                                                 intent_token=intent_token,key=key,grants_input_authority=False,
                                                 application_consumption_observed=False)
                            identity_status,actuation_id=hold_identity.on_down(code,key,intent_token,owner_owned_before,classified_status=='CONFIRMED_PHYSICAL_DOWN',event_context)
                            measurement=dict(edge='down',classification=classified_status,bracket=bracket,actuation_id=actuation_id,
                                identity_status=identity_status,pre_sample=pre,post_sample=post,
                                press_request_ns=press_request_ns,sync_return_ns=sync_return_ns,
                                adapter_edge=_edge_for_adapter('down',bracket,actuation_id),
                                grants_input_authority=False,application_consumption_observed=False)
                            result = dict(event='input_admission', key=key, admitted_ns=admitted,
                                          input_ack_ns=input_ack_ns, valid_until_ns=lease.deadline,
                                          physical_key_measurement=measurement)
                        else:
                            # Cleanup from an old intent must never release a newer hold.
                            if code in held and held[code] is not lease:
                                raise ValueError('key belongs to another intent')
                            owner_owned = code in held
                            pre = sample_key_state(code)
                            release_attempted = owner_owned
                            release_request_ns=time.perf_counter_ns()
                            if owner_owned:
                                xtest.fake_input(d, X.KeyRelease, code)
                                d.sync()
                                sync_return_ns=time.perf_counter_ns()
                                del held[code]
                            else:
                                sync_return_ns=release_request_ns
                            post = sample_key_state(code)
                            intent_token=lease_intent_token(lease)
                            bracket=None; classified_status='PHYSICAL_SAMPLE_UNAVAILABLE'; physical_interval=None
                            if pre['available'] and post['available']:
                                classified_status,_=_classify_release(owner_owned,pre['down'],release_attempted,release_attempted,post['down'])
                                physical_interval=[pre['finished_ns'],post['finished_ns']] if classified_status=='CONFIRMED_PHYSICAL_UP' else None
                                if intent_token is not None:
                                    bracket=dict(status=classified_status,physical_up_interval=physical_interval,
                                                 release_id=f'{self.owner_id}:r{revision}:up:{code}',owner_id=self.owner_id,
                                                 intent_token=intent_token,key=key,grants_input_authority=False,
                                                 application_consumption_observed=False)
                            identity_status,actuation_id=hold_identity.on_up(code,key,intent_token,classified_status=='CONFIRMED_PHYSICAL_UP')
                            measurement=dict(edge='up',classification=classified_status,bracket=bracket,actuation_id=actuation_id,
                                identity_status=identity_status,pre_sample=pre,post_sample=post,
                                release_attempted=release_attempted,release_request_ns=release_request_ns,sync_return_ns=sync_return_ns,
                                adapter_edge=_edge_for_adapter('up',bracket,actuation_id),
                                grants_input_authority=False,application_consumption_observed=False)
                            result = dict(event='input_release_measurement',key=key,valid_until_ns=getattr(lease,'deadline',None),
                                          physical_key_measurement=measurement,grants_input_authority=False)
                    else:
                        raise ValueError('unknown input operation')
                    if continuation and isinstance(result,dict):
                        result.update(continuation=True,owner_id=self.owner_id,revision=revision)
                    reply.append((True, result))
                except Exception as exc:
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
