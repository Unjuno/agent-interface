"""Prospective opt-in comparison; no model/game execution on import."""
import os
import hashlib
from pathlib import Path
import portable_controller_entry_05 as previous

EXPECTED_CONTROLLER = 'a0bcfa076970b7cf6d048155478952958280b7958e0bbe486c0f1f12a55e4f0e'

def install():
    controller = previous.install()
    if hashlib.sha256(Path(controller.__file__).read_bytes()).hexdigest() != EXPECTED_CONTROLLER:
        raise ValueError('comparison controller hash mismatch')
    arm = os.environ['COMPARISON_ARM']
    if arm not in ('guarded_cover', 'coast_reference'):
        raise ValueError('explicit comparison arm required')
    if arm == 'coast_reference':
        # Existing no-authority coast path and fresh final admission stay intact.
        controller.reusable_cover = lambda decisions: ([], None, None)
    return controller

if __name__ == '__main__':
    install().main()
