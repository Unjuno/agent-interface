# Result: C02 current-v39 owner keymap witness

Allocation `MAP01-V39-OWNER-KEYMAP-WITNESS-C02-20261004-01` used one candidate invocation and one independent auditor invocation. The candidate exited 0; the auditor returned `PASS_V39_XVFB_KEYMAP_WITNESS_CONSTRUCTION_SCOPED` with every check true.

Both distinct W-key occurrences produced the expected 32-byte XQueryKeymap sequence `false, true, false`. Each had one admission record and one per-key release transition with `ordinary_release_candidate=true`, matching intent and owner identities, empty owned-key state after the batch, and `owner_transition_verified=true`. Each backend key-up was followed by the v10 owner's explicit release boundary before the post-up server keymap query. The final close record verified empty keys and buttons. Xvfb TCP was disabled; the process exited 0 and its display socket and lock were removed.

The exact source snapshots were current-main InputOwner v10 (main `13bab54`), the v39 backend from PR #7355 head `2b9cc1a`, and the transition wrapper from PR #7376 head `cf4904c`. The actual `Backend.raw()` method and InputOwner thread ran. The v39 backend base initializer was stubbed; no game, model, GPU, physical keyboard, or application ran.

C01 remains a separate preserved failed candidate. It omitted the owner release boundary after raw key-up and stopped at the first down with `ValueError('another intent owns input')`. C02 changed that lifecycle protocol, used a new allocation ID, and passed its own frozen audit; neither allocation is overwritten or retried.

The guest could not create a network namespace (`unshare -n` returned 1 with `Operation not permitted`). The candidate made no network calls and Xvfb listened on no TCP port, but guest networking remained enabled. The actual C02 interpreter and packages are recorded in `ENVIRONMENT.json`.

Setup note: the frozen `SETUP.md` says the venv path was `/tmp/v39-keymap-c02-venv`. Restarting the guest cleared its tmpfs `/tmp`; before C02 freeze, the pinned packages were reinstalled into `/home/taka/.local/venvs/v39-keymap-c02`, which is the interpreter path captured in `ENVIRONMENT.json` and used for both invocations. The setup note discrepancy is retained and disclosed here.

This is scoped virtual X11 construction evidence only. It does not establish physical input, application consumption, useful feedback onset, bounded recovery, latency, matched-condition benefit, task effect, safety, or live threat exposure; it does not close Issue #59.
