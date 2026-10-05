"""V15 release-batch backend with per-key post-sync X-server samples."""

from doom_owner_thread_release_batch_backend_v1 import Backend as Previous
from input_transition_owner_v5 import InputOwner


class Backend(Previous):
    """Use the V5 owner receipt while retaining V1 batch custody semantics."""

    InputOwner = InputOwner

