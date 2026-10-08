"""Backend choice helper for the V15 scorer plus optional V39 edge measurement."""


def preserve_opt_in_measurement_backend(base, release_batch_backend, argv):
    """Do not replace v12's A01 backend after its CLI parser selects it."""
    if "--per-key-input-measurement" not in argv:
        base.Backend = release_batch_backend
    return base.Backend
