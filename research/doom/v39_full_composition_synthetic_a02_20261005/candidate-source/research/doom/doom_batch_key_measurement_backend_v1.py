"""V15 opt-in keymap brackets on the current ordered-release backend."""
from doom_owner_thread_release_batch_backend_v1 import Backend as Previous, suite
from input_owner_v12 import InputOwner
from pathlib import Path
import key_edge_measurement_v1
from input_transition_owner_v4 import InputOwner as TransitionOwner


class Backend(Previous):
    measurement_sources = (Path(key_edge_measurement_v1.__file__),)

    def __init__(self, session, out, emit, signal_readers):
        # Keep the current owner, transition validation and delivery ledger.
        # The startup source guard checks the actual raw InputOwner above.
        def measured_owner(display_name):
            return InputOwner(display_name, measure_key_edges=True)

        def transition_owner(display_name):
            return TransitionOwner(display_name, _owner_cls=measured_owner)

        super().__init__(session, out, emit, signal_readers,
                         _owner_cls=transition_owner)
