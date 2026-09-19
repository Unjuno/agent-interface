"""Research input owner: one X11 connection, independent of capture and logging.

This is scheduler-dependent deadline enforcement, not hard real-time control.
No user callback, image work, file write or stdout write runs on this thread.
"""
import queue
import threading
import time
from Xlib import X, XK, display
from Xlib.ext import xtest
from executor_v3 import Cancelled, DecisionRequired


class InputOwner:
    def __init__(self, display_name):
        self.requests = queue.Queue()
        self.records = []
        self.ready = threading.Event()
        self.error = None
        self.closed = False
        self.display_name = display_name
        self.thread = threading.Thread(target=self._run, name='input-owner')
        self.thread.start()
        self.ready.wait()
        if self.error is not None:
            self.thread.join()
            raise self.error

    def call(self, operation, lease=None, key=None):
        if self.closed:
            raise RuntimeError('input owner closed')
        done = threading.Event()
        reply = []
        self.requests.put((operation, lease, key, done, reply))
        done.wait()
        ok, result = reply[0]
        if not ok:
            raise result
        return result

    def close(self):
        if not self.closed:
            try:
                self.call('close')
            finally:
                self.closed = True
                self.thread.join()

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
        fault = None
        self.ready.set()

        def focus_id():
            value=d.get_input_focus().focus
            return value.id if hasattr(value,'id') else value

        def invalid_focus(lease):
            if not hasattr(lease,'expected_focus'):
                raise ValueError('observed input focus required')
            actual=focus_id()
            return actual != lease.expected_focus

        def hit_surface(lease, x, y):
            # Surface ID must come from the observation, not the requested point.
            surface = getattr(lease, 'expected_surface', None)
            if type(surface) is not int or surface in (0, 1):
                raise ValueError('observed client surface required for pointer input')
            root = d.screen().root
            node = root
            for _ in range(32):
                child = node.translate_coords(root, x, y).child
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
            if getattr(lease, 'focus_invalid', False) or invalid_focus(lease):
                lease.focus_invalid = True
                raise DecisionRequired()
            if not hit_surface(lease, x, y):
                raise DecisionRequired()
            lease.check()
            if lease.cancel.is_set():
                raise Cancelled()

        def release(reason):
            nonlocal active
            for code in list(held):
                xtest.fake_input(d, X.KeyRelease, code)
            for button in list(buttons):
                xtest.fake_input(d, X.ButtonRelease, button)
            d.sync()
            mask = d.screen().root.query_pointer().mask
            buttons_down = [b for b in touched_buttons if mask & (X.Button1Mask << (b-1))]
            bitmap = d.query_keymap()
            down = [code for code in touched if bitmap[code // 8] & (1 << (code % 8))]
            record = dict(event='owner_release', reason=reason, verified=not down and not buttons_down, buttons_down=buttons_down,
                          keys_down=down, verified_ns=time.perf_counter_ns(),
                          valid_until_ns=active.deadline if active else None)
            self.records.append(record)
            if down or buttons_down:
                raise RuntimeError('owner release not verified: ' + repr(down))
            buttons.clear()
            touched_buttons.clear()
            held.clear()
            touched.clear()
            active = None
            return record

        try:
            while True:
                # Check before dequeue so a busy request queue cannot starve expiry.
                if active is not None:
                    expired = time.perf_counter_ns() >= active.deadline
                    changed=invalid_focus(active)
                    surface_changed=False
                    if buttons and not changed:
                        point=d.screen().root.query_pointer()
                        surface_changed=not hit_surface(active,point.root_x,point.root_y)
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
                    if op in ('release', 'close'):
                        if op == 'release' and active is not None and active is not lease:
                            raise ValueError('release belongs to another intent')
                        result = release(op)
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
                            active = lease
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
                            active = lease
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
                                xtest.fake_input(d, X.KeyRelease, code)
                                d.sync()
                                del held[code]
                            result = None
                    else:
                        raise ValueError('unknown input operation')
                    reply.append((True, result))
                except Exception as exc:
                    reply.append((False, exc))
                finally:
                    done.set()
                if closing:
                    break
        finally:
            d.close()
