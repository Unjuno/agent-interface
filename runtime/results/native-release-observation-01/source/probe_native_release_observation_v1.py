"""Owned-Xvfb diagnostic controls; not a reproduction of the earlier failure."""
import argparse
import json
from pathlib import Path
import time

from Xlib import X, XK, display
from Xlib.ext import xtest

from native_release_observation_v1 import observe_release_failure
from run_native_six_task_self_use_v1 import PrivateSession
from runtime.backends.x11_v1.backend import X11Backend


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    session = backend = controller = None
    keycode = None
    rows = []
    def save():
        (args.out/'observations.json').write_text(json.dumps(rows, indent=2)+'\n')
    try:
        session = PrivateSession()
        backend = X11Backend(session.name, {})
        controller = display.Display(session.name)
        keycode = controller.keysym_to_keycode(XK.string_to_keysym('a'))
        assert keycode > 0
        (args.out/'fixture.json').write_text(json.dumps({
            'display': session.name, 'keycode': keycode, 'fixture_input_emissions_planned': 4,
            'diagnostic_input_emissions_expected': 0,
            'reproduces_prior_release_failure': False}, indent=2)+'\n')
        for condition in ('initial_up', 'held_key_and_left', 'released_by_fixture'):
            if condition == 'held_key_and_left':
                xtest.fake_input(controller, X.KeyPress, keycode)
                xtest.fake_input(controller, X.ButtonPress, 1)
            elif condition == 'released_by_fixture':
                xtest.fake_input(controller, X.ButtonRelease, 1)
                xtest.fake_input(controller, X.KeyRelease, keycode)
            controller.sync()
            time.sleep(.05)  # Fixture settling, not a proposed runtime recovery.
            record = observe_release_failure(backend)
            rows.append({'condition': condition, 'record': record})
            save()
            assert record['backend_emissions_before'] == record['backend_emissions_after'] == 0
            for sample in record['samples']:
                assert sample['status'] == 'observed'
                assert sample['keycodes_down'] == ([keycode] if condition == 'held_key_and_left' else [])
                assert sample['core_buttons_down'] == ([1] if condition == 'held_key_and_left' else [])
        (args.out/'result.json').write_text(json.dumps({'status': 'scoped_pass', 'conditions': 3,
            'samples': 9, 'prior_failure_cause_identified': False}, indent=2)+'\n')
    finally:
        # Explicit fixture cleanup, separate from the read-only diagnostic.
        try:
            if controller is not None:
                try:
                    if keycode is not None:
                        xtest.fake_input(controller, X.ButtonRelease, 1)
                        xtest.fake_input(controller, X.KeyRelease, keycode)
                        controller.sync()
                finally:
                    controller.close()
        finally:
            try:
                if backend is not None:
                    backend.close()
            finally:
                if session is not None:
                    session.close()
                    (args.out/'cleanup.json').write_text(json.dumps([
                        {'pid': p.pid, 'returncode': p.poll()} for p in session.procs], indent=2)+'\n')


if __name__ == '__main__':
    main()
