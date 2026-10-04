"""Opt-in scoped handles over the existing X11 runtime session.

One persistent, explicitly owned native connection and one private handle store.
Shared by the native research callers and portable Python API; X11 only.
"""
from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import time
import uuid

from PIL import Image
from .handles import TargetHandleStore
from .history import ObservationHistory
from runtime.backends.x11_v1.backend import X11Backend, X11BackendError
from runtime.backends.x11_v1.session import X11RuntimeSession
from runtime.core_v1.contract import SCHEMA_PROGRAM
from runtime.core_v1.compiled_gui import ObservationAssociationChanged
from runtime.cli_v1.api import dispatch_in_session
from runtime.cli_v1.observe import observe_in_session


class CaptureBindingChanged(X11BackendError, ObservationAssociationChanged):
    """Exact before/after binding mismatch; retains the existing X11 error type."""


def read_window_title(connection, window):
    """Read a public title cue; never establishes input authority or task success."""
    for name in ('_NET_WM_NAME', '_NET_WM_VISIBLE_NAME'):
        value = window.get_full_property(connection.intern_atom(name),
                                         connection.intern_atom('UTF8_STRING'))
        if value is not None:
            return bytes(value.value).decode('utf-8', errors='strict')
    return window.get_wm_name()

class _GuardedBackend(X11Backend):
    def key_state(self, key, down):
        # Text expands to key chords, so check each new press, including a
        # modifier's following key. Releases must remain possible after expiry.
        if (down and self.owner.active is not None and self.owner.deadline is not None
                and time.monotonic_ns() >= self.owner.deadline):
            raise X11BackendError('native target guard lease expired')
        # A wait or an earlier modifier can outlive the original focus binding.
        # Do not refocus automatically: release remains possible after focus loss.
        if down and self.owner.active is not None and not self.owner._focus_within_target():
            raise X11BackendError('focused window is outside guarded target before key press')
        if (down and self.owner.active is not None
                and getattr(self.owner, '_input_guard', None) is not None
                and self.owner.active[0] == self.owner._input_guard['alias']):
            self.owner.check('before_key_press:' + str(key))
        return super().key_state(key, down)

    def _wait_update(self, timeout_ms):
        deadline = self.owner.deadline if self.owner.active is not None else None
        if deadline is None:
            return super()._wait_update(timeout_ms)
        end = time.monotonic_ns() + timeout_ms * 1_000_000
        while True:
            now = time.monotonic_ns()
            if now >= deadline:
                raise X11BackendError('native target guard lease expired during wait')
            if now >= end:
                return
            time.sleep((min(end, deadline) - now) / 1_000_000_000)

    def focus(self, target):
        if self.owner.active is not None:
            self.owner.check("before_focus")
            if not self.owner._focus_within_target():
                raise X11BackendError('focused window is outside guarded target')
            # GTK applications may focus an InputOnly child. Refocusing the
            # top-level window changes the exact binding we just validated.
            return
        return super().focus(target)

    def pointer_move(self, target, frame, x, y):
        point = self.owner.check("before_move")["point"]
        super().pointer_move(target, "screen_physical_px", *point)
        self.owner.moved_point = point

    def pointer_button(self, button, down):
        if down:
            point = self.owner.check("before_press")["point"]
            pointer = self.root.query_pointer()
            if point != self.owner.moved_point or [pointer.root_x, pointer.root_y] != point:
                raise X11BackendError("guarded point moved after pointer motion")
        return super().pointer_button(button, down)


class NativeHandleBridge:
    def __init__(self, display_name, targets, target, out):
        self.out = Path(out)
        self.out.mkdir(parents=True, exist_ok=False)
        self.target = target
        self.scope = "native-x11:" + uuid.uuid4().hex
        self.store = TargetHandleStore(self.scope)
        self.sequence = 0
        self.history = ObservationHistory()
        self.checks = []
        self.active = None
        self._input_guard = None
        self.additional_checks = []
        self.moved_point = None
        self.deadline = None
        self.review_required = False
        self.binding_revision = 0
        self.used_aliases = set()
        self.backend = _GuardedBackend(display_name, dict(targets))
        self.backend.owner = self
        try:
            self.backend.configure_capture_artifacts(self.out / "images", retain_rgb=True)
            self.session = X11RuntimeSession(self.backend)
        except Exception:
            self.backend.close()
            raise

    def close(self):
        self.backend.close()

    def _save(self, name, value):
        (self.out / name).write_text(json.dumps(value, indent=2) + "\n")

    def _binding(self):
        focus = self.backend.d.get_input_focus().focus
        geometry = self.backend.geometry(self.target)
        return {"focus": getattr(focus, "id", focus),
                "surface": self.backend.targets[self.target].id,
                "geometry": [geometry[k] for k in ("x", "y", "width", "height")]}

    def _focus_within_target(self, window_id=None):
        """Read-only X11 ancestry, not title/PID similarity or input authority."""
        if window_id is None:
            window_id = self.backend.targets[self.target].id
        try:
            focus = self.backend.d.get_input_focus().focus
            seen = set()
            for _ in range(64):
                identifier = getattr(focus, 'id', None)
                if type(identifier) is not int or identifier <= 0 or identifier in seen:
                    return False
                if identifier == window_id:
                    return True
                seen.add(identifier)
                focus = focus.query_tree().parent
        except Exception:
            return False
        return False

    def observe(self):
        started_ns = time.monotonic_ns()
        before = self._binding()
        screen = self.backend.d.screen()
        report = observe_in_session(self.session, target=self.target,
            frame="screen_physical_px",
            region=[0, 0, screen.width_in_pixels, screen.height_in_pixels])
        public_returned_ns = time.monotonic_ns()
        self._save("public-observation-" + report["observation_id"] + ".json", report)
        if report["status"] != "returned":
            raise X11BackendError("public observation failed; inspect retained report: "
                                  + str(report.get("error", report["status"])))
        native = report["observation"]
        after = self._binding()
        if before != after:
            self.review_required = True
            self._save("capture-binding-changed-" + report["observation_id"] + ".json", {
                "reason": "association_changed", "before": before, "after": after,
                "public_report": "public-observation-" + report["observation_id"] + ".json",
                "last_valid_sequence": self.sequence, "authority_granted": False,
                "replay_allowed": False})
            raise CaptureBindingChanged("binding changed during native capture")
        binding_checked_ns = time.monotonic_ns()
        artifact = native["artifact"]
        data = Path(artifact["path"]).read_bytes()
        if (hashlib.sha256(data).hexdigest() != artifact["sha256"] or
                artifact["source_raw_sha256"] != native["sha256"]):
            raise X11BackendError("native artifact identity mismatch")
        artifact_verified_ns = time.monotonic_ns()
        # Use the very RGB pixels that produced this verified PNG. No new
        # capture, older-frame reuse or reduced target revalidation occurs.
        image = self.backend.take_capture_rgb(artifact)
        decoded_ns = time.monotonic_ns()
        self.sequence += 1
        observation = {"sequence": self.sequence, "observation_id": report["observation_id"],
                       "binding_revision": self.binding_revision,
                       "capture_ns": native["capture_started_ns"],
                       "image_source": "exact_capture_rgb_handoff",
                       "pointer_binding": before, "native": native,
                       # Ends before history publication; not model-visible latency.
                       "timing_ns": {"started": started_ns,
                                     "public_returned": public_returned_ns,
                                     "binding_checked": binding_checked_ns,
                                     "artifact_verified": artifact_verified_ns,
                                     "decoded": decoded_ns}}
        self.history[self.sequence] = (observation, image)
        self._save(f"observation-{self.sequence}.json", observation)
        return observation

    def focused_client_window(self):
        """Find the nearest managed ancestor of actual focus, without input.

        A GTK InputOnly child is not the application's surface. The WM's client
        list and a bounded ancestry walk identify a candidate for explicit
        review; this lookup neither changes binding nor grants authority.
        """
        try:
            d = self.backend.d
            clients = self.backend.root.get_full_property(
                d.intern_atom('_NET_CLIENT_LIST'), d.intern_atom('WINDOW'))
            if clients is None or clients.format != 32:
                return None
            managed = {int(identifier) for identifier in clients.value if int(identifier) > 0}
            focus = d.get_input_focus().focus
            seen = set()
            for _ in range(64):
                identifier = getattr(focus, 'id', None)
                if type(identifier) is not int or identifier <= 0 or identifier in seen:
                    return None
                if identifier in managed:
                    return identifier
                seen.add(identifier)
                focus = focus.query_tree().parent
        except Exception:
            return None
        return None

    def mint(self, alias, source_sequence, point, *, region_size=(24, 38)):
        """Legacy offset-only grounding; use mint_reference for expiry metadata."""
        return self.mint_reference(alias, source_sequence, point, region_size=region_size)['offset']

    def mint_reference(self, alias, source_sequence, point, *, region_size=(24, 38)):
        """Ground a finite alias without capture, renewal, input or authority."""
        if getattr(getattr(self, 'session', None), 'recovery_required', False):
            raise X11BackendError('input recovery required before minting')
        if getattr(self, 'review_required', False):
            raise X11BackendError('window review required before minting')
        if alias in getattr(self, 'used_aliases', set()):
            raise ValueError('target alias cannot be reused across window reviews')
        # The caller must name an exact previously delivered observation.
        observation, image = self.history[source_sequence]
        w, h = region_size
        box = [point[0] - w // 2, point[1] - h // 2, w, h]
        minted_ns = time.monotonic_ns()
        result = self.store.mint(alias, "window_content", box, observation, image,
                                 minted_ns, ttl_ms=300000, freshness_ms=1500,
                                 search_radius=0, allowed_transformations=("window_translation",))
        self.used_aliases = getattr(self, 'used_aliases', set()) | {alias}
        self._save("mint-" + alias + ".json", result)
        return {'offset': [w // 2, h // 2], 'lifetime': {
            'clock': 'time.monotonic_ns', 'minted_ns': minted_ns,
            'expires_ns': result['expires_ns'], 'capture_freshness_ms': 1500,
            'authority_granted': False,
            'scope': 'Same execution host clock only. Alias expiry is not capture freshness, pixel validity or input authority. Retained lookup does not renew it.'}}

    def activate_window(self, *, window_id, source_sequence, current_binding_revision,
                        expires_at_ns, timeout_ms):
        """Explicitly activate the registered target; require a later window review.

        Uses ordinary admission and the caller's lease. No editing, automatic
        replay, alias renewal or successful-task assertion follows activation.
        """
        if (self.active is not None or self.session.recovery_required or
                type(window_id) is not int or window_id != self.backend.targets[self.target].id or
                type(source_sequence) is not int or source_sequence < 1 or source_sequence != self.sequence or
                type(current_binding_revision) is not int or current_binding_revision != self.binding_revision or
                type(expires_at_ns) is not int or expires_at_ns < 1 or
                type(timeout_ms) is not int or not 0 <= timeout_ms <= 2000):
            return {'status': 'refused', 'error': 'ACTIVATION_CONTEXT_MISMATCH',
                    'input_dispatched': False, 'task_success': None, 'replay_allowed': False}
        program = {
            'schema': SCHEMA_PROGRAM, 'program_id': 'activate-' + uuid.uuid4().hex,
            'source': {'observation_seq': source_sequence, 'binding_revision': current_binding_revision},
            'authority': {'lease_id': self.scope.replace(':', '-'), 'expires_at_ns': expires_at_ns},
            'terminal': {'release_all_required': True},
            'ops': [{'op': 'activate', 'target': self.target, 'timeout_ms': timeout_ms},
                    {'op': 'release_all'}],
        }
        self._save('program-' + program['program_id'] + '.json', program)
        previous_review_required = self.review_required
        self.active = ('activation', None)
        try:
            # Any thrown exception here may follow a WM request. Keep editing
            # blocked until the caller explicitly reviews the current window.
            self.review_required = True
            report = dispatch_in_session(self.session, program,
                current_observation_seq=source_sequence,
                current_binding_revision=current_binding_revision)
            self._save('public-dispatch-' + program['program_id'] + '.json', report)
            if report['status'] != 'returned':
                return {'status': 'activation_failed', 'error': report.get('error'),
                        'dispatch_report': report, 'effect_status': 'unknown',
                        'task_success': None, 'replay_allowed': False}
            result = report['result']
            if result.get('status') == 'refused':
                self.review_required = previous_review_required
            return result
        finally:
            self.active = None

    def review_window(self, window_id):
        """Explicit read-only handoff on this connection; revoke old aliases.

        The caller chooses the window to review. This never focuses a window,
        restores input authority or imports handles from the previous scope.
        A failed review leaves mint/click disabled until a successful review.
        """
        if self.active is not None:
            raise RuntimeError('cannot review another window during input')
        if type(window_id) is not int or window_id <= 0:
            raise ValueError('explicit positive window ID required')
        previous_scope = self.scope
        previous_revision = getattr(self, 'binding_revision', 0)
        self.binding_revision = previous_revision + 1
        previous_window = self.backend.targets[self.target].id
        self.review_required = True
        self.scope = 'native-x11:' + uuid.uuid4().hex
        self.store = TargetHandleStore(self.scope)
        self.history.clear()
        row = {'status': 'needs_review', 'authority_granted': False,
               'input_dispatched': False, 'previous_scope': previous_scope,
               'previous_binding_revision': previous_revision, 'binding_revision': self.binding_revision,
               'scope': self.scope, 'previous_window_id': previous_window,
               'requested_window_id': window_id, 'started_ns': time.monotonic_ns()}
        try:
            if not self._focus_within_target(window_id):
                raise X11BackendError('requested review window is not focused')
            self.backend.targets[self.target] = self.backend.d.create_resource_object('window', window_id)
            observation = self.observe()
            if (getattr(self.backend.d.get_input_focus().focus, 'id', None) != observation['pointer_binding']['focus']
                    or not self._focus_within_target(window_id)):
                raise X11BackendError('focus changed during window review')
            row.update(status='reviewed', observation=observation)
            self.review_required = False
        except Exception as error:
            # observe may have retained an image before the final focus check.
            # It cannot become a minting source after a failed handoff.
            self.history.clear()
            row['error'] = repr(error)
        row['ended_ns'] = time.monotonic_ns()
        self._save('window-review-' + uuid.uuid4().hex + '.json', row)
        return row

    def _window_title(self):
        window = self.backend.targets[self.target]
        d = self.backend.d
        return read_window_title(d, window)

    def feedback(self, expected_title, *, rejected_titles=(), timeout_ms=2000):
        """Read-only application cue plus native image; never a task score.

        Title matching is a caller-selected application convention. It grants
        no input authority and cannot establish durable application effect.
        """
        if self.active is not None:
            raise RuntimeError("cannot wait for feedback during guarded input")
        if type(timeout_ms) is not int or not 0 <= timeout_ms <= 10000:
            raise ValueError("feedback timeout must be 0..10000 ms")
        if not isinstance(expected_title, str) or not expected_title:
            raise ValueError("explicit nonempty expected title required")
        rejected_titles = tuple(rejected_titles)
        if any(not isinstance(t, str) or not t or t == expected_title for t in rejected_titles):
            raise ValueError("distinct nonempty rejected titles required")
        started = time.monotonic_ns()
        deadline = started + timeout_ms * 1_000_000
        samples = []
        row = {'status': 'pending', 'task_success': None, 'authority_granted': False,
               'input_dispatched': False, 'expected_title': expected_title,
               'rejected_titles': list(rejected_titles), 'samples': samples,
               'started_ns': started}
        try:
            while True:
                title = self._window_title()
                binding = self._binding()
                samples.append({'known_ns': time.monotonic_ns(), 'title': title,
                                'binding': binding})
                candidate = ('matched' if title == expected_title else
                             'rejected' if title in rejected_titles else 'pending')
                focused = self._focus_within_target()
                if candidate != 'pending' or not focused or time.monotonic_ns() >= deadline:
                    observation = self.observe()
                    after_title = self._window_title()
                    row.update(observation=observation, title=title, after_title=after_title)
                    # A changed title/binding during capture cannot certify a cue.
                    stable = (title == after_title and binding == observation['pointer_binding']
                              and binding == self._binding() and self._focus_within_target())
                    row['status'] = candidate if stable and focused else 'needs_review'
                    break
                time.sleep(min(.05, max(0, (deadline-time.monotonic_ns())/1e9)))
        except Exception as error:
            row.update(status='needs_review', error=repr(error))
        row['ended_ns'] = time.monotonic_ns()
        self._save('feedback-' + uuid.uuid4().hex + '.json', row)
        return row

    @contextmanager
    def input_guard(self, alias, offset, *, tail, verify):
        """Explicit additional check for one frozen keyboard program.

        Trusted synchronous caller code, never authority or automatic renewal.
        The caller serializes this context with all other use of the owner.
        The callback must return exactly True; releases always bypass it.
        """
        if self.active is not None or getattr(self, '_input_guard', None) is not None:
            raise RuntimeError('input guard requires an idle, unguarded bridge')
        if self.review_required or self.session.recovery_required:
            raise RuntimeError('input guard requires reviewed, recovered bridge')
        if (not isinstance(alias, str) or not alias or not isinstance(offset, list)
                or len(offset) != 2 or any(type(v) is not int or v < 0 for v in offset)
                or not isinstance(tail, (list, tuple)) or not tail or not callable(verify)):
            raise ValueError('explicit alias, integer offset, frozen tail and callable check required')
        self._input_guard = {'alias':alias, 'offset':deepcopy(offset),
                             'tail':deepcopy(list(tail)), 'verify':verify,
                             'scope':self.scope, 'revision':self.binding_revision}
        try:
            yield
        finally:
            self._input_guard = None

    def _check_additional_input(self, stage, observation):
        guard = getattr(self, '_input_guard', None)
        if guard is None or self.active[0] != guard['alias']:
            return
        sequence = self.sequence
        active, deadline = deepcopy(self.active), self.deadline
        source, image = self.history[sequence]
        row = {'stage':stage, 'observation_sequence':sequence,
               'scope':self.scope, 'binding_revision':self.binding_revision,
               'started_ns':time.monotonic_ns(), 'eligible':False,
               'authority_granted':False}
        try:
            if self.scope != guard['scope'] or self.binding_revision != guard['revision']:
                raise X11BackendError('input guard binding changed')
            decision = guard['verify'](stage, deepcopy(source), image.copy())
            if decision is not True:
                raise X11BackendError('additional input dependency refused')
            if (self.sequence != sequence or self.active != active
                    or self.deadline != deadline or self._input_guard is not guard
                    or self.scope != guard['scope']
                    or self.binding_revision != guard['revision']
                    or self._binding() != observation['pointer_binding']
                    or not self._focus_within_target()
                    or self.review_required or self.session.recovery_required):
                raise X11BackendError('input guard association changed during check')
            if self.deadline is not None and time.monotonic_ns() >= self.deadline:
                raise X11BackendError('input guard lease expired during check')
            # The trusted callback can consume the captured source's freshness
            # budget. Re-resolve against the same RGB/history at the new time;
            # no recapture, renewal or callback retry is allowed here.
            after = self.store.resolve_point(self.active[0], self.active[1], observation,
                image, time.monotonic_ns(), session_scope=self.scope)
            if not after['eligible']:
                raise X11BackendError('native target guard expired during additional check: ' + after['status'])
            row['eligible'] = True
        except Exception as error:
            row['error'] = repr(error)
            raise X11BackendError('additional input dependency unavailable: ' + repr(error)) from error
        finally:
            row['ended_ns'] = time.monotonic_ns()
            self.additional_checks.append(row)

    def check(self, stage):
        if self.active is None:
            raise X11BackendError("no active native target guard")
        if self.deadline is not None and time.monotonic_ns() >= self.deadline:
            raise X11BackendError("native target guard lease expired")
        observation = self.observe()
        outcome = self.store.resolve_point(self.active[0], self.active[1], observation,
            self.history[self.sequence][1], time.monotonic_ns(), session_scope=self.scope)
        row = {"stage": stage, "observation_sequence": self.sequence, **outcome}
        self.checks.append(row)
        if not outcome["eligible"]:
            raise X11BackendError("native target guard refused: " + outcome["status"])
        if self.deadline is not None and time.monotonic_ns() >= self.deadline:
            raise X11BackendError("native target guard lease expired during capture")
        self._check_additional_input(stage, observation)
        return outcome

    def click(self, alias, offset, *, tail=(), expires_at_ns=None):
        return self._run_guarded(alias, offset, tail=tail, interaction='click', expires_at_ns=expires_at_ns)

    def move(self, alias, offset, *, tail=(), expires_at_ns=None):
        """Guarded pointer motion only; hover may change the screen. No click."""
        return self._run_guarded(alias, offset, tail=tail, interaction='move', expires_at_ns=expires_at_ns)

    def keyboard(self, alias, offset, *, tail, expires_at_ns=None):
        """Continue in the currently focused, visually guarded context; no click."""
        return self._run_guarded(alias, offset, tail=tail, interaction='keyboard', expires_at_ns=expires_at_ns)

    def _run_guarded(self, alias, offset, *, tail, interaction, expires_at_ns=None):
        if self.active is not None:
            raise RuntimeError("native bridge already executing")
        if getattr(getattr(self, 'session', None), 'recovery_required', False):
            row = {'status': 'refused', 'error': 'INPUT_RECOVERY_REQUIRED',
                   'recovery_required': True, 'input_dispatched': False}
            self._save('result-' + uuid.uuid4().hex + '.json', row)
            return row
        if getattr(self, 'review_required', False):
            row = {'status': 'refused', 'error': 'WINDOW_REVIEW_REQUIRED', 'input_dispatched': False}
            self._save('result-' + uuid.uuid4().hex + '.json', row)
            return row
        guard = getattr(self, '_input_guard', None)
        protected = guard is not None and alias == guard['alias']
        if protected:
            if self.scope != guard['scope'] or self.binding_revision != guard['revision']:
                raise X11BackendError('input guard binding changed before dispatch')
            if (interaction != 'keyboard' or offset != guard['offset']
                    or list(tail) != guard['tail']):
                raise ValueError('protected input differs from frozen keyboard program')
        # An outer method may shorten, never renew, this input lease. The caller
        # must use this process's monotonic clock domain (not wall-clock time).
        if expires_at_ns is not None:
            if type(expires_at_ns) is not int or expires_at_ns < 1:
                raise ValueError('expires_at_ns must be a positive monotonic integer')
            if time.monotonic_ns() >= expires_at_ns:
                row = {'status': 'refused', 'error': 'CALLER_DEADLINE_EXPIRED',
                       'input_dispatched': False}
                self._save('result-' + uuid.uuid4().hex + '.json', row)
                return row
        # Motion can change hover state. It grants no press or keyboard authority.
        from runtime.core_v1.sequence import expand_text_gaps
        # Core permits 128 ops including focus, action and terminal release.
        tail = expand_text_gaps(tail, max_ops={'click':123, 'move':125, 'keyboard':126}[interaction])[0]
        if interaction == 'move' and any(op.get('op') not in {'wait_update', 'observe'} for op in tail):
            raise ValueError('guarded move tail permits only wait_update and observe')
        if any(op.get("op") not in {"text", "key_chord", "wait_update", "observe"} for op in tail):
            raise ValueError("unsupported guarded-click tail")
        if interaction == 'keyboard' and not any(op.get('op') in {'text', 'key_chord'} for op in tail):
            raise ValueError('keyboard continuation requires explicit keyboard input')
        self.active = (alias, offset)
        self.checks = []
        self.additional_checks = []
        self.deadline = time.monotonic_ns() + 5_000_000_000
        if expires_at_ns is not None:
            self.deadline = min(self.deadline, expires_at_ns)
        self.moved_point = None
        try:
            try:
                point = self.check("before_admission")["point"]
                if time.monotonic_ns() >= self.deadline:
                    raise X11BackendError('native target guard lease expired before dispatch')
            except Exception as error:
                row = {"status": "refused", "error": repr(error), "input_dispatched": False}
            else:
                pointer_ops = ([] if interaction == 'keyboard' else [
                    {"op": "pointer_move", "frame": "screen_physical_px", "x": point[0], "y": point[1]}])
                if interaction == 'click':
                    pointer_ops.extend([
                        {"op": "pointer_button", "button": "left", "down": True},
                        {"op": "pointer_button", "button": "left", "down": False}])
                program = {
                    "schema": SCHEMA_PROGRAM, "program_id": "guarded-" + uuid.uuid4().hex,
                    "source": {"observation_seq": self.sequence,
                               "binding_revision": self.binding_revision},
                    "authority": {"lease_id": self.scope.replace(":", "-"), "expires_at_ns": self.deadline},
                    "terminal": {"release_all_required": True},
                    "ops": [{"op": "focus", "target": self.target},
                            *pointer_ops,
                            *tail, {"op": "release_all"}],
                }
                self._save("program-" + program["program_id"] + ".json", program)
                report = dispatch_in_session(self.session, program,
                    current_observation_seq=self.sequence,
                    current_binding_revision=self.binding_revision)
                self._save("public-dispatch-" + program["program_id"] + ".json", report)
                if report["status"] != "returned":
                    raise RuntimeError("public dispatch failed; inspect retained report: "
                                       + str(report.get("error", report["status"])))
                row = report["result"]
            row["guard_checks"] = list(self.checks)
            if protected:
                row["additional_input_checks"] = list(self.additional_checks)
            self._save("result-" + uuid.uuid4().hex + ".json", row)
            return row
        finally:
            self.active = None
            self.deadline = None
