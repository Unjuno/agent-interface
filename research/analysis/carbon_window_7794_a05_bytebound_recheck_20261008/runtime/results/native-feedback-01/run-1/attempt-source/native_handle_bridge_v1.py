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
        observation = {"sequence": self.sequence, "capture_ns": native["capture_started_ns"],
                       "pointer_binding": before, "native": native}
        self.history[self.sequence] = (observation, image)
        self._save(f"observation-{self.sequence}.json", observation)
        return observation

    def mint(self, alias, source_sequence, point, *, region_size=(24, 38)):
        # The caller must name an exact previously delivered observation.
        observation, image = self.history[source_sequence]
        w, h = region_size
        box = [point[0] - w // 2, point[1] - h // 2, w, h]
        result = self.store.mint(alias, "window_content", box, observation, image,
                                 time.monotonic_ns(), ttl_ms=300000, freshness_ms=1500,
                                 search_radius=0, allowed_transformations=("window_translation",))
        self._save("mint-" + alias + ".json", result)
        return [w // 2, h // 2]

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
        target = self.backend.targets[self.target]
        samples = []
        row = {'status': 'pending', 'task_success': None, 'authority_granted': False,
               'input_dispatched': False, 'expected_title': expected_title,
               'rejected_titles': list(rejected_titles), 'samples': samples,
               'started_ns': started}
        try:
            while True:
                title = target.get_wm_name()
                binding = self._binding()
                samples.append({'known_ns': time.monotonic_ns(), 'title': title,
                                'binding': binding})
                candidate = ('matched' if title == expected_title else
                             'rejected' if title in rejected_titles else 'pending')
                focused = binding['focus'] == binding['surface']
                if candidate != 'pending' or not focused or time.monotonic_ns() >= deadline:
                    observation = self.observe()
                    after_title = target.get_wm_name()
                    row.update(observation=observation, title=title, after_title=after_title)
                    # A changed title/binding during capture cannot certify a cue.
                    stable = (title == after_title and binding == observation['pointer_binding']
                              and binding == self._binding())
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
                    "source": {"observation_seq": self.sequence, "binding_revision": 0},
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
                                            current_binding_revision=0)
            row["guard_checks"] = list(self.checks)
            self._save("result-" + uuid.uuid4().hex + ".json", row)
            return row
        finally:
            self.active = None
            self.deadline = None
