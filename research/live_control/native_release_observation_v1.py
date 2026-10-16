"""Read-only follow-up evidence after failed release; never recovery authority."""
import time

from Xlib import X


def observe_release_failure(backend):
    started = time.monotonic_ns()
    before = backend.emissions
    row = {'schema': 'agent-interface/native-release-observation-v1',
           'authority_granted': False, 'input_dispatched': False,
           'clears_recovery_required': False, 'started_ns': started, 'samples': [],
           'coverage': {'keycodes': [8, 255], 'core_buttons': [1, 2, 3, 4, 5],
                        'extended_buttons_observed': False, 'atomic_snapshot': False}}
    # A bounded number of read-only queries. Xlib calls themselves are not
    # preempted; offsets are sampling targets, not a hard transport timeout.
    masks = [(1, X.Button1Mask), (2, X.Button2Mask), (3, X.Button3Mask),
             (4, X.Button4Mask), (5, X.Button5Mask)]
    for offset_ms in (0, 10, 50):
        delay = (started + offset_ms * 1_000_000 - time.monotonic_ns()) / 1e9
        if delay > 0:
            time.sleep(delay)
        sample = {'requested_offset_ms': offset_ms, 'started_ns': time.monotonic_ns()}
        try:
            keymap = backend.d.query_keymap()
            if len(keymap) != 32:
                raise ValueError('expected 256-bit X11 keymap')
            sample['keymap_known_ns'] = time.monotonic_ns()
            sample['keycodes_down'] = [code for code in range(8, 256)
                                      if keymap[code // 8] & (1 << (code % 8))]
            pointer = backend.root.query_pointer()
            sample.update(pointer_known_ns=time.monotonic_ns(), pointer_mask=int(pointer.mask),
                          core_buttons_down=[button for button, mask in masks if pointer.mask & mask],
                          status='observed')
        except Exception as error:
            sample.update(status='unavailable', error=repr(error))
        row['samples'].append(sample)
        if sample['status'] == 'unavailable':
            break
    row.update(ended_ns=time.monotonic_ns(), backend_emissions_before=before,
               backend_emissions_after=backend.emissions)
    # A counter mismatch invalidates the no-input assertion instead of masking it.
    row['input_dispatched'] = False if before == backend.emissions else None
    return row
