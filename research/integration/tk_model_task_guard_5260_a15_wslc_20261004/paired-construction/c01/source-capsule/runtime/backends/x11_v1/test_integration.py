from __future__ import annotations
import json, os, subprocess, sys, tempfile, time, unittest
from pathlib import Path

from runtime.core_v1.contract import SCHEMA_PROGRAM, office_readiness
from runtime.backends.x11_v1.backend import X11Backend
from runtime.backends.x11_v1.session import X11RuntimeSession


def make_program(pid: str, *, seq=7, revision=3, expires=None, text="office"):
    if expires is None:
        expires = time.monotonic_ns() + 30_000_000_000
    return {
        "schema": SCHEMA_PROGRAM,
        "program_id": pid,
        "source": {"observation_seq": seq, "binding_revision": revision},
        "authority": {"lease_id": "x11-integration", "expires_at_ns": expires},
        "terminal": {"release_all_required": True},
        "ops": [
            {"op": "focus", "target": "fixture"},
            {"op": "pointer_move", "frame": "window_client", "x": 50, "y": 55},
            {"op": "pointer_button", "button": "left", "down": True},
            {"op": "pointer_button", "button": "left", "down": False},
            {"op": "wait_update", "timeout_ms": 50},
            {"op": "key_chord", "keys": ["Home"]},
            {"op": "key_chord", "keys": ["SHIFT", "End"]},
            {"op": "text", "text": text},
            {"op": "key_chord", "keys": ["CTRL", "S"]},
            {"op": "wait_update", "timeout_ms": 40},
            {"op": "observe", "frame": "window_client", "x": 0, "y": 0, "w": 300, "h": 140},
            {"op": "release_all"},
        ],
    }


@unittest.skipUnless(os.environ.get("DISPLAY"), "requires X11 DISPLAY")
class X11IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        root = Path(cls.tmp.name)
        cls.meta = root / "meta.json"; cls.effect = root / "effect.json"; cls.events = root / "events.jsonl"
        cls.proc = subprocess.Popen([
            sys.executable, "-m", "runtime.backends.x11_v1.fixture_app",
            "--meta", str(cls.meta), "--effect", str(cls.effect), "--events", str(cls.events),
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)
        deadline = time.time() + 5
        while time.time() < deadline and not cls.meta.exists():
            if cls.proc.poll() is not None:
                raise RuntimeError(f"fixture exited {cls.proc.returncode}")
            time.sleep(0.05)
        if not cls.meta.exists(): raise RuntimeError("fixture metadata timeout")
        window_id = json.loads(cls.meta.read_text())["window_id"]
        cls.backend = X11Backend(os.environ["DISPLAY"], {"fixture": window_id})
        cls.session = X11RuntimeSession(cls.backend)

    @classmethod
    def tearDownClass(cls):
        try: cls.backend.close()
        except Exception: pass
        cls.proc.terminate()
        try: cls.proc.wait(timeout=2)
        except subprocess.TimeoutExpired: cls.proc.kill()
        cls.tmp.cleanup()

    def setUp(self):
        self.effect.unlink(missing_ok=True)

    def test_manifest_is_ready_with_narrow_text_detail(self):
        manifest = self.backend.manifest()
        self.assertTrue(office_readiness(manifest)["ready"])
        self.assertIn("strict ASCII", manifest["capabilities"]["input.text"]["detail"])

    def test_failure_after_real_button_press_retains_prefix_and_releases(self):
        class FailAfterPress(X11Backend):
            def pointer_button(self, button, down):
                super().pointer_button(button, down)
                if down:
                    raise RuntimeError("injected failure after native press")

        target = self.backend.targets["fixture"].id
        backend = FailAfterPress(os.environ["DISPLAY"], {"fixture": target})
        try:
            row = X11RuntimeSession(backend).dispatch(make_program("partial-press"),
                current_observation_seq=7, current_binding_revision=3)
            self.assertEqual(row["status"], "execution_failed")
            execution = row["execution"]
            self.assertEqual(execution["completed_ops"], [0, 1])
            self.assertEqual(execution["failed_op"], 2)
            self.assertEqual(execution["program_emissions"], 3)  # move, press, recovery release
            self.assertEqual(execution["releases"][-1]["buttons_down"], [])
            self.assertTrue(execution["releases"][-1]["verified"])
            self.assertFalse(self.effect.exists())
        finally:
            backend.close()

    def test_unverified_native_release_quarantines_persistent_session(self):
        class LostRelease(X11Backend):
            suppress_release = True
            def pointer_button(self, button, down):
                super().pointer_button(button, down)
                if down:
                    raise RuntimeError("injected failure after native press")
            def release_all(self):
                if self.suppress_release:
                    return {"verified": False, "error": "injected release request failure"}
                return super().release_all()

        backend = LostRelease(os.environ["DISPLAY"],
                              {"fixture": self.backend.targets["fixture"].id})
        session = X11RuntimeSession(backend)
        trace = {}
        try:
            first = session.dispatch(make_program("lost-release"),
                current_observation_seq=7, current_binding_revision=3)
            trace["first"] = first
            self.assertEqual(first["status"], "execution_failed")
            self.assertTrue(first["recovery_required"])
            # A separate connection observes the server state, not the receipt.
            trace["independent_buttons_before_cleanup"] = self.backend._physical_buttons_down()
            self.assertIn("left", trace["independent_buttons_before_cleanup"])
            emissions = backend.emissions
            second = session.dispatch(make_program("blocked", seq=8, revision=4),
                current_observation_seq=8, current_binding_revision=4)
            trace["second"] = second
            self.assertEqual(second["error"], "INPUT_RECOVERY_REQUIRED")
            self.assertEqual(backend.emissions, emissions)
            self.assertFalse(self.effect.exists())
            # Cleanup remains possible, but cannot silently reset the owner.
            backend.suppress_release = False
            trace["explicit_cleanup"] = backend.release_all()
            trace["independent_buttons_after_cleanup"] = self.backend._physical_buttons_down()
            self.assertEqual(trace["independent_buttons_after_cleanup"], [])
            trace["third"] = session.dispatch(make_program("still-blocked"),
                current_observation_seq=7, current_binding_revision=3)
            self.assertEqual(trace["third"]["error"], "INPUT_RECOVERY_REQUIRED")
        finally:
            backend.suppress_release = False
            backend.close()
            if os.environ.get("AI_RELEASE_TRACE"):
                Path(os.environ["AI_RELEASE_TRACE"]).write_text(json.dumps(trace, indent=2) + "\n")

    def test_valid_program_has_independent_effect_and_verified_release(self):
        before = self.backend.emissions
        row = self.session.dispatch(make_program("valid"), current_observation_seq=7, current_binding_revision=3)
        self.assertEqual(row["status"], "completed")
        self.assertGreater(self.backend.emissions, before)
        self.assertTrue(self.effect.exists())
        effect = json.loads(self.effect.read_text())
        self.assertEqual(effect, {"saved": True, "text": "office"})
        releases = row["execution"]["releases"]
        self.assertTrue(releases and releases[-1]["verified"])
        self.assertEqual(releases[-1]["keys_down"], [])
        self.assertEqual(releases[-1]["buttons_down"], [])
        self.assertEqual(len(row["execution"]["observations"]), 1)

    def test_synchronous_pointer_grab_keeps_recovery_explicit(self):
        from Xlib import X, display
        class FailAfterPress(X11Backend):
            def pointer_button(self, button, down):
                super().pointer_button(button, down)
                if down:
                    raise RuntimeError('injected failure after native press')

        observer = display.Display(os.environ['DISPLAY'])
        target = self.backend.targets['fixture'].id
        window = observer.create_resource_object('window', target)
        backend = FailAfterPress(os.environ['DISPLAY'], {'fixture': target})
        session = X11RuntimeSession(backend)
        try:
            # A real passive synchronous grab freezes subsequent pointer events.
            # The independent connection owns both the grab and its release.
            window.grab_button(1, X.AnyModifier, False, X.ButtonPressMask,
                               X.GrabModeSync, X.GrabModeAsync, X.NONE, X.NONE)
            observer.sync()
            program = make_program('synchronous-grab')
            result = session.dispatch(program, current_observation_seq=7,
                                      current_binding_revision=3)
            self.assertEqual(result['status'], 'execution_failed')
            self.assertFalse(result['execution']['releases'][-1]['verified'])
            self.assertTrue(observer.screen().root.query_pointer().mask & X.Button1Mask)
            self.assertTrue(session.recovery_required)
            emissions = backend.emissions

            # Allow the already queued release to run; send no additional input.
            observer.allow_events(X.AsyncPointer, X.CurrentTime)
            window.ungrab_button(1, X.AnyModifier)
            observer.sync()
            deadline = time.monotonic() + .5
            masks = []
            while True:
                mask = observer.screen().root.query_pointer().mask
                masks.append(mask)
                if not mask & X.Button1Mask or time.monotonic() >= deadline:
                    break
                time.sleep(.001)  # test observer only, not a production wait
            self.assertFalse(masks[-1] & X.Button1Mask, masks)
            self.assertEqual(backend.emissions, emissions)
            self.assertTrue(session.recovery_required)
            blocked = session.dispatch(program, current_observation_seq=7,
                                       current_binding_revision=3)
            self.assertEqual(blocked['error'], 'INPUT_RECOVERY_REQUIRED')
            self.assertEqual(backend.emissions, emissions)
            recovered = session.recover_input()
            self.assertEqual(recovered['status'], 'input_recovered')
            self.assertFalse(recovered['replay_allowed'])
            self.assertIsNone(recovered['task_success'])
            self.assertFalse(session.recovery_required)
            self.assertFalse(self.effect.exists())
        finally:
            observer.allow_events(X.AsyncPointer, X.CurrentTime)
            window.ungrab_button(1, X.AnyModifier)
            observer.sync()
            backend.release_all()
            backend.close()
            observer.close()

    def test_stale_observation_emits_zero_input(self):
        before = self.backend.emissions
        row = self.session.dispatch(make_program("stale", seq=6), current_observation_seq=7, current_binding_revision=3)
        self.assertEqual(row["error"], "STALE_OBSERVATION")
        self.assertEqual(self.backend.emissions, before)
        self.assertFalse(self.effect.exists())

    def test_supported_punctuation_has_exact_independent_effect(self):
        payload = "http://127.0.0.1:8765/a-._ A"
        row = self.session.dispatch(make_program("punctuation", text=payload),
                                    current_observation_seq=7, current_binding_revision=3)
        self.assertEqual(row["status"], "completed")
        self.assertEqual(json.loads(self.effect.read_text()), {"saved": True, "text": payload})
        self.assertTrue(row["execution"]["releases"][-1]["verified"])

    def test_stale_binding_emits_zero_input(self):
        before = self.backend.emissions
        row = self.session.dispatch(make_program("binding", revision=2), current_observation_seq=7, current_binding_revision=3)
        self.assertEqual(row["error"], "STALE_BINDING")
        self.assertEqual(self.backend.emissions, before)

    def test_expired_lease_emits_zero_input(self):
        before = self.backend.emissions
        row = self.session.dispatch(make_program("expired", expires=1), current_observation_seq=7, current_binding_revision=3, now_ns=2)
        self.assertEqual(row["error"], "LEASE_EXPIRED")
        self.assertEqual(self.backend.emissions, before)

    def test_verify_refuses_before_save_and_session_can_continue(self):
        program = make_program("unsupported-verify", text="must-not-save")
        program["ops"].insert(-1, {"op": "verify", "predicate": "saved"})
        before = self.backend.emissions
        row = self.session.dispatch(program, current_observation_seq=7, current_binding_revision=3)
        self.assertEqual(row["status"], "refused")
        self.assertEqual(row["error"], "BACKEND_CONSTRAINT")
        self.assertIn("verify predicates are not implemented", row["detail"])
        self.assertEqual(self.backend.emissions, before)
        self.assertFalse(self.effect.exists())
        self.assertTrue(row["release"]["verified"])
        continued = self.session.dispatch(make_program("explicit-save", text="review"),
            current_observation_seq=7, current_binding_revision=3)
        self.assertEqual(continued["status"], "completed")
        self.assertEqual(json.loads(self.effect.read_text()), {"saved": True, "text": "review"})

    def test_backend_specific_invalid_text_emits_zero_input(self):
        program = make_program("bad-text", text="ok!")
        before = self.backend.emissions
        row = self.session.dispatch(program, current_observation_seq=7, current_binding_revision=3)
        self.assertEqual(row["status"], "refused")
        self.assertEqual(row["error"], "BACKEND_CONSTRAINT")
        self.assertIn("unsupported text character", row["detail"])
        self.assertEqual(self.backend.emissions, before)
        self.assertFalse(self.effect.exists())
        self.assertTrue(row["release"]["verified"])
        self.assertEqual(row["release"]["keys_down"], [])
        self.assertEqual(row["release"]["buttons_down"], [])


@unittest.skipUnless(os.environ.get('DISPLAY'), 'requires X11 DISPLAY')
class X11MappingIntegrationTests(unittest.TestCase):
    # Mapping is server-wide state. Keep its fixture lifetime separate from
    # the ordinary input tests so their existing Tk clients cannot retain it.
    def test_midprogram_keymap_change_stops_before_suffix_and_save(self):
        """Use only the caller-owned private test DISPLAY, restoring its map."""
        display = os.environ['DISPLAY']
        original = subprocess.run(['xkbcomp', display, '-'], capture_output=True, text=True, check=True).stdout
        try:
            for initial, changed in (('jp', 'us'), ('us', 'jp')):
                with self.subTest(initial=initial, changed=changed), tempfile.TemporaryDirectory() as scratch:
                    # A refused program leaves its real prefix in the app. Own a
                    # separate app so this test cannot change another test's edit state.
                    root = Path(scratch); meta = root/'meta.json'; effect = root/'effect.json'
                    app = subprocess.Popen([sys.executable, '-m', 'runtime.backends.x11_v1.fixture_app', '--meta', str(meta), '--effect', str(effect)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    backend = None
                    try:
                        deadline = time.monotonic() + 5
                        while not meta.exists():
                            if app.poll() is not None or time.monotonic() > deadline:
                                raise RuntimeError('private remap fixture not ready')
                            time.sleep(.02)
                        subprocess.run(['setxkbmap', '-display', display, '-layout', initial], check=True, capture_output=True)
                        actor = []
                        class RemapDuringWait(X11Backend):
                            def _wait_update(self, milliseconds):
                                if milliseconds == 111:
                                    result = subprocess.run(['setxkbmap', '-display', display, '-layout', changed], capture_output=True)
                                    actor.append(result.returncode)
                                    if result.returncode:
                                        raise RuntimeError('private keymap actor failed')
                                super()._wait_update(milliseconds)
                        backend = RemapDuringWait(display, {'fixture': json.loads(meta.read_text())['window_id']})
                        program = make_program('midprogram-' + initial + '-' + changed, text='a')
                        program['ops'][4]['timeout_ms'] = 100
                        program['ops'][8:8] = [{'op': 'wait_update', 'timeout_ms': 111}, {'op': 'text', 'text': '_'}]
                        row = X11RuntimeSession(backend).dispatch(program, current_observation_seq=7, current_binding_revision=3)
                        self.assertEqual(actor, [0])
                        self.assertEqual(row['status'], 'execution_failed')
                        self.assertEqual(row['execution']['failed_op'], 9)
                        self.assertEqual(row['execution']['completed_ops'], list(range(9)))
                        self.assertIn('keyboard mapping changed', row['execution']['error'])
                        self.assertFalse(effect.exists())
                        release = row['execution']['releases'][-1]
                        self.assertTrue(release['verified'])
                        self.assertEqual(release['keys_down'], [])
                        self.assertEqual(release['buttons_down'], [])
                    finally:
                        if backend is not None:
                            backend.close()
                        app.terminate(); app.wait(timeout=5)
        finally:
            subprocess.run(['xkbcomp', '-', display], input=original, text=True, capture_output=True, check=True)


if __name__ == "__main__": unittest.main()
