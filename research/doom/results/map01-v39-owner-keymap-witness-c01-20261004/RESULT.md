# Result: C01 current-v39 owner keymap witness

Allocation `MAP01-V39-OWNER-KEYMAP-WITNESS-C01-20261004-01` used one candidate invocation and one independent auditor invocation. The candidate exited 1 at its first `backend.raw("w", True)` with `ValueError('another intent owns input')`; the auditor returned `FAIL_OR_HOLD_V39_KEYMAP_WITNESS`. Preserve the start receipt, raw record, and failed audit as the original result.

The failure came from the isolated harness omitting the v10 owner lifecycle boundary. Raw key-up clears the key hold, while the active lease remains until `InputOwner.release`. C01 attempted its second occurrence with a new lease without releasing the first lease. The verified owner cleanup record shows no held key or button, and Xvfb exited 0 during cleanup. The protocol did not produce two occurrences or keymap witnesses.

The distinct C02 allocation adds the explicit owner release boundary after each raw key-up and passes its frozen construction audit. C01 was not rerun or overwritten.

This result establishes neither backend failure nor physical input, application consumption, useful feedback, bounded recovery, latency, task effect, safety, or threat exposure.
