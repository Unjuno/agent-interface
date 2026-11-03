"""Opt-in read-only X client; never injects input or closes the input client."""
import queue
import threading
import time
import secrets
from types import SimpleNamespace
from Xlib import X, Xatom, display
from .process_identity import read_linux_x11_process_identity_details


class QueryUnavailable(RuntimeError):
    pass


def focus_within_target(connection, window_id, *, raise_errors=False):
    try:
        focus = connection.get_input_focus().focus
        seen = set()
        for _ in range(64):
            identifier = getattr(focus,'id',None)
            if type(identifier) is not int or identifier <= 0 or identifier in seen:
                return False
            if identifier == window_id:
                return True
            seen.add(identifier)
            focus = focus.query_tree().parent
    except Exception:
        if raise_errors: raise
        return False
    return False


class X11TargetQueries:
    def __init__(self, display_name):
        self.connection = display.Display(display_name)
        self._windows = {}
        self._lifecycle_retired = False

    def _window_incarnation(self, xid):
        if self._lifecycle_retired:
            raise QueryUnavailable('window lifecycle reader retired')
        try:
            if type(xid) is not int or xid <= 1:
                raise ValueError('explicit target window required')
            window = self.connection.create_resource_object('window', xid)
            if xid not in self._windows:
                errors = []
                window.change_attributes(event_mask=X.StructureNotifyMask,
                                         onerror=lambda *args: errors.append(True))
                self.connection.sync()
                if errors:
                    raise QueryUnavailable('window subscription failed')
                self._windows[xid] = secrets.token_hex(32)
            attrs = window.get_attributes()
            mask = attrs.your_event_mask
            if type(mask) is not int or not mask & X.StructureNotifyMask:
                raise QueryUnavailable('direct window subscription missing')
            self.connection.sync()
            stable = {X.UnmapNotify, X.MapNotify, X.ReparentNotify,
                      X.ConfigureNotify, X.GravityNotify, X.CirculateNotify}
            for _ in range(256):
                if not self.connection.pending_events():
                    break
                event = self.connection.next_event()
                kind = event.type
                if type(kind) is not int or event.send_event not in (False, 0):
                    raise QueryUnavailable('synthetic or malformed lifecycle event')
                # MappingNotify is delivered independently of window selection.
                if kind == X.MappingNotify:
                    continue
                window_id = getattr(event.window, 'id', event.window)
                receiver = getattr(event.event, 'id', event.event)
                if (type(window_id) is not int or window_id not in self._windows
                        or receiver != window_id or kind not in stable):
                    raise QueryUnavailable('destroyed window or unqualified lifecycle event')
            if self.connection.pending_events():
                raise QueryUnavailable('window lifecycle event budget exceeded')
            return self._windows[xid]
        except BaseException as error:
            self._lifecycle_retired = True
            raise QueryUnavailable('window lifecycle unavailable; fresh session required') from error

    def _bounded_text_property(self, window, name, *, max_bytes=256):
        expected_type = (self.connection.intern_atom('UTF8_STRING')
            if name == '_NET_WM_NAME' else Xatom.STRING)
        prop = window.get_property(self.connection.intern_atom(name),
            expected_type, 0, (max_bytes + 3) // 4)
        if prop is None:
            return None
        if (prop.property_type != expected_type or prop.format != 8 or prop.bytes_after != 0
                or len(prop.value) > max_bytes):
            raise QueryUnavailable('window metadata property is malformed or oversized')
        return bytes(prop.value).decode('utf-8', errors='strict')

    def _window_reference_property(self, window, name):
        prop = window.get_property(self.connection.intern_atom(name),
            Xatom.WINDOW, 0, 1)
        if prop is None:
            return None
        if (prop.property_type != Xatom.WINDOW or prop.format != 32
                or prop.bytes_after != 0 or len(prop.value) != 1):
            raise QueryUnavailable('window reference property is malformed')
        value = prop.value[0]
        if type(value) is not int or not 1 < value < 2**32:
            raise QueryUnavailable('window reference property is invalid')
        return value

    def _window_metadata(self, xid):
        """Return bounded read-only chooser cues; none grants input authority."""
        if type(xid) is not int or not 1 < xid < 2**32:
            raise ValueError('explicit target window required')
        started_ns = time.monotonic_ns()
        incarnation = self._window_incarnation(xid)
        focused_before = focus_within_target(self.connection, xid, raise_errors=True)
        process = read_linux_x11_process_identity_details(self.connection, xid)
        window = self.connection.create_resource_object('window', xid)
        attrs = window.get_attributes()
        parent = window.query_tree().parent
        transient_id = self._window_reference_property(window, 'WM_TRANSIENT_FOR')
        class_value = self._bounded_text_property(window, 'WM_CLASS')
        wm_class = None
        if class_value is not None:
            pieces = class_value.split('\0')
            if (len(pieces) != 3 or pieces[-1] != ''
                    or any(not piece or len(piece) > 128 for piece in pieces[:2])):
                raise QueryUnavailable('window class is malformed')
            wm_class = pieces[:2]
        title = self._bounded_text_property(window, '_NET_WM_NAME')
        role = self._bounded_text_property(window, 'WM_WINDOW_ROLE')
        process_after = read_linux_x11_process_identity_details(self.connection, xid)
        current_incarnation = self._window_incarnation(xid)
        focused_after = focus_within_target(self.connection, xid, raise_errors=True)
        if (current_incarnation != incarnation
                or process_after['process_incarnation']
                    != process['process_incarnation']):
            raise QueryUnavailable('window or process changed during metadata query')
        observed_ns = time.monotonic_ns()
        parent_id = getattr(parent, 'id', parent)
        map_state = getattr(attrs, 'map_state', None)
        return {'schema':'agent-interface/x11-window-metadata-cues-v1',
            'query_started_monotonic_ns':started_ns,
            'observed_monotonic_ns':observed_ns,
            'xid':xid, 'parent_xid':parent_id,
            'transient_for_xid':transient_id,
            'wm_class':wm_class, 'title_cue':title, 'role_cue':role,
            'mapped':map_state == X.IsViewable,
            'process_incarnation':process['process_incarnation'],
            'process_generation':process['process_generation'],
            'process_pid':process['pid'],
            'process_start_ticks':process['start_ticks'],
            'window_incarnation':incarnation,
            'focused_before':focused_before,
            'focused_after':focused_after,
            'input_authority':False, 'authenticated_role':False}

    def _windows_for_process(self, pid, title_hint):
        """Return bounded viewable descendants with an exact XRes process PID.

        This is discovery evidence for an explicit later ``review_window``;
        the title is a search cue only and does not select/focus a window or
        grant input authority. Descendant traversal includes WM frame nesting.
        """
        if type(pid) is not int or pid <= 0:
            raise ValueError('positive process PID required')
        if (type(title_hint) is not str or not title_hint
                or len(title_hint) > 128 or not title_hint.isprintable()):
            raise ValueError('bounded printable title hint required')
        from Xlib import X
        root = self.connection.screen().root
        pending = [(root, 0, False, None)]
        seen = set()
        result = []
        while pending:
            parent, depth, inherited_hint, hint_xid = pending.pop()
            if depth >= 32:
                raise QueryUnavailable('window tree depth limit exceeded')
            children = parent.query_tree().children
            for child in children:
                xid = getattr(child, 'id', None)
                if type(xid) is not int or not 1 < xid < 2**32:
                    raise QueryUnavailable('window tree contains malformed XID')
                if xid in seen:
                    raise QueryUnavailable('window tree contains duplicate XID')
                seen.add(xid)
                if len(seen) > 4096:
                    raise QueryUnavailable('window tree enumeration limit exceeded')
                window = self.connection.create_resource_object('window', xid)
                attrs = window.get_attributes()
                matched_hint = inherited_hint
                matched_hint_xid = hint_xid
                if getattr(attrs, 'map_state', None) == X.IsViewable:
                    title = self._bounded_text_property(window, '_NET_WM_NAME')
                    if title_hint in (title or ''):
                        matched_hint = True
                        matched_hint_xid = xid
                if matched_hint and getattr(attrs, 'map_state', None) == X.IsViewable:
                    identity = read_linux_x11_process_identity_details(
                        self.connection, xid)
                    if identity.get('pid') == pid:
                        metadata = self._window_metadata(xid)
                        if metadata.get('process_pid') != pid:
                            raise QueryUnavailable(
                                'window process changed during discovery')
                        metadata['discovery_title_hint'] = title_hint
                        metadata['discovery_title_xid'] = matched_hint_xid
                        result.append(metadata)
                        if len(result) > 128:
                            raise QueryUnavailable(
                                'matching process window limit exceeded')
                if depth + 1 < 32:
                    pending.append((window, depth + 1, matched_hint, matched_hint_xid))
        return result

    def read(self, operation, xid):
        if operation == 'window_incarnation':
            return self._window_incarnation(xid)
        if operation == 'focus_id':
            focus = self.connection.get_input_focus().focus
            return getattr(focus, 'id', focus)
        if operation == 'focus':
            return focus_within_target(self.connection,xid,raise_errors=True)
        if operation == 'process_identity':
            return read_linux_x11_process_identity_details(
                self.connection,xid)['process_generation']
        if operation == 'process_incarnation':
            return read_linux_x11_process_identity_details(
                self.connection,xid)['process_incarnation']
        if operation == 'window_metadata':
            return self._window_metadata(xid)
        if operation == 'windows_for_process':
            if (type(xid) is not dict or set(xid) != {'pid','title_hint'}):
                raise ValueError('process window query requires exact PID and title hint')
            return self._windows_for_process(xid['pid'],xid['title_hint'])
        raise ValueError('unknown target query')

    def close(self):
        self._lifecycle_retired = True
        self.connection.close()


class TargetQueryWorker:
    """One client/thread, one request; retirement is sticky and never waits on I/O.

    A timed-out client closes on its own thread after its blocked call returns.
    This cannot interrupt X, force close, or establish a physical release bound.
    """
    def __init__(self, factory, *, before_read=None):
        if before_read is not None and not callable(before_read):
            raise TypeError('before_read must be callable when supplied')
        self.factory = factory
        self.before_read = before_read
        self.lock = threading.Lock()
        self.queue = queue.Queue(maxsize=1)
        self.thread = None
        self.current = None
        self.retired = False
        self.close_error = None

    def snapshot(self):
        with self.lock:
            return dict(retired=self.retired, pending=self.current is not None and not self.current.done.is_set(),
                        thread_alive=self.thread is not None and self.thread.is_alive(),close_error=self.close_error)

    def close(self):
        with self.lock:
            self.retired = True
            try: self.queue.put_nowait(None)
            except queue.Full: pass
        return self.snapshot()

    def _run(self):
        reader = None
        try:
            while True:
                job = self.queue.get()
                with self.lock:
                    if self.retired or job is None: break
                try:
                    if reader is None: reader = self.factory()
                    # Opening may have blocked after the waiter retired this client.
                    # Do not begin another I/O operation when that open returns.
                    with self.lock:
                        if self.retired: raise QueryUnavailable('target query retired during open')
                    if self.before_read is not None:
                        self.before_read(job.operation, job.xid)
                    # A test barrier may outlive the caller's deadline. Once
                    # the waiter retires this worker, never start the delayed
                    # X request; its thread remains quarantined until the
                    # barrier returns and this check is reached.
                    with self.lock:
                        if self.retired:
                            raise QueryUnavailable('target query retired before read')
                    job.value = reader.read(job.operation,job.xid)
                except BaseException as error:
                    job.error = error
                finally:
                    job.done.set()
                with self.lock:
                    if self.retired: break
        finally:
            if reader is not None:
                try: reader.close()
                except BaseException as error:
                    with self.lock: self.close_error = repr(error)

    def read(self, operation, xid, *, deadline_ns, cancelled):
        if type(deadline_ns) is not int:
            raise QueryUnavailable('original target-query deadline required')
        if cancelled() or time.monotonic_ns() >= deadline_ns:
            self.close()
            raise QueryUnavailable('target query cancelled or original deadline expired')
        with self.lock:
            if self.retired or self.current is not None:
                raise QueryUnavailable('target query worker retired or occupied')
            job = SimpleNamespace(operation=operation,xid=xid,done=threading.Event(),value=None,error=None)
            self.current = job
            self.queue.put_nowait(job)
            if self.thread is None:
                self.thread = threading.Thread(target=self._run,name='guarded-read-only-query',daemon=True)
                try: self.thread.start()
                except BaseException as error:
                    self.retired = True
                    job.done.set()
                    raise QueryUnavailable('target query worker did not start') from error
        try:
            while True:
                with self.lock:
                    if self.retired: raise QueryUnavailable('target query retired')
                if cancelled() or time.monotonic_ns() >= deadline_ns:
                    raise QueryUnavailable('target query cancelled or original deadline expired')
                if job.done.wait(.005):
                    if cancelled() or time.monotonic_ns() >= deadline_ns:
                        raise QueryUnavailable('late target query discarded')
                    if job.error is not None:
                        raise QueryUnavailable('target query failed') from job.error
                    with self.lock:
                        if self.retired: raise QueryUnavailable('target query retired')
                        self.current = None
                    return job.value
        except BaseException:
            self.close()
            raise
