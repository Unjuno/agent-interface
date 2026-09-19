"""Experimental bridge: existing scoped handles over the promoted X11 session.

One persistent, explicitly owned native connection and one private handle store.
This module is not promoted or included in the portable distribution.
"""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import time
import uuid

from PIL import Image
from scoped_target_handle_v3 import TargetHandleStore
from runtime.backends.x11_v1.backend import X11Backend, X11BackendError
from runtime.backends.x11_v1.session import X11RuntimeSession
from runtime.core_v1.contract import SCHEMA_PROGRAM


class _GuardedBackend(X11Backend):
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
        self.history = {}
        self.checks = []
        self.active = None
        self.moved_point = None
        self.deadline = None
        self.review_required = False
        self.binding_revision = 0
        self.used_aliases = set()
        self.backend = _GuardedBackend(display_name, dict(targets))
        self.backend.owner = self
        try:
            self.backend.configure_capture_artifacts(self.out / "images")
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
        before = self._binding()
        screen = self.backend.d.screen()
        native = self.backend.capture(self.target, "screen_physical_px", 0, 0,
                                      screen.width_in_pixels, screen.height_in_pixels)
        after = self._binding()
        if before != after:
            raise X11BackendError("binding changed during native capture")
        artifact = native["artifact"]
        data = Path(artifact["path"]).read_bytes()
        if (hashlib.sha256(data).hexdigest() != artifact["sha256"] or
                artifact["source_raw_sha256"] != native["sha256"]):
            raise X11BackendError("native artifact identity mismatch")
        with Image.open(io.BytesIO(data)) as opened:
            image = opened.convert("RGB")
        self.sequence += 1
        observation = {"sequence": self.sequence, "binding_revision": self.binding_revision,
                       "capture_ns": native["capture_started_ns"],
                       "pointer_binding": before, "native": native}
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
        result = self.store.mint(alias, "window_content", box, observation, image,
                                 time.monotonic_ns(), ttl_ms=300000, freshness_ms=1500,
                                 search_radius=0, allowed_transformations=("window_translation",))
        self.used_aliases = getattr(self, 'used_aliases', set()) | {alias}
        self._save("mint-" + alias + ".json", result)
        return [w // 2, h // 2]

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
        value = window.get_full_property(d.intern_atom('_NET_WM_NAME'),
                                         d.intern_atom('UTF8_STRING'))
        if value is not None:
            return bytes(value.value).decode('utf-8', errors='strict')
        return window.get_wm_name()

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

    def check(self, stage):
        if self.active is None:
            raise X11BackendError("no active native target guard")
        if self.deadline is not None and time.monotonic_ns() > self.deadline:
            raise X11BackendError("native target guard lease expired")
        observation = self.observe()
        outcome = self.store.resolve_point(self.active[0], self.active[1], observation,
            self.history[self.sequence][1], time.monotonic_ns(), session_scope=self.scope)
        row = {"stage": stage, "observation_sequence": self.sequence, **outcome}
        self.checks.append(row)
        if not outcome["eligible"]:
            raise X11BackendError("native target guard refused: " + outcome["status"])
        if self.deadline is not None and time.monotonic_ns() > self.deadline:
            raise X11BackendError("native target guard lease expired during capture")
        return outcome

    def click(self, alias, offset, *, tail=()):
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
        # One guarded click per program; no unguarded pointer in the tail.
        if any(op.get("op") not in {"text", "key_chord", "wait_update", "observe"} for op in tail):
            raise ValueError("unsupported guarded-click tail")
        self.active = (alias, offset)
        self.checks = []
        self.deadline = time.monotonic_ns() + 5_000_000_000
        self.moved_point = None
        try:
            try:
                point = self.check("before_admission")["point"]
            except Exception as error:
                row = {"status": "refused", "error": repr(error), "input_dispatched": False}
            else:
                program = {
                    "schema": SCHEMA_PROGRAM, "program_id": "guarded-" + uuid.uuid4().hex,
                    "source": {"observation_seq": self.sequence,
                               "binding_revision": self.binding_revision},
                    "authority": {"lease_id": self.scope.replace(":", "-"), "expires_at_ns": self.deadline},
                    "terminal": {"release_all_required": True},
                    "ops": [{"op": "focus", "target": self.target},
                            {"op": "pointer_move", "frame": "screen_physical_px", "x": point[0], "y": point[1]},
                            {"op": "pointer_button", "button": "left", "down": True},
                            {"op": "pointer_button", "button": "left", "down": False},
                            *tail, {"op": "release_all"}],
                }
                self._save("program-" + program["program_id"] + ".json", program)
                row = self.session.dispatch(program, current_observation_seq=self.sequence,
                                            current_binding_revision=self.binding_revision)
            row["guard_checks"] = list(self.checks)
            self._save("result-" + uuid.uuid4().hex + ".json", row)
            return row
        finally:
            self.active = None
            self.deadline = None
