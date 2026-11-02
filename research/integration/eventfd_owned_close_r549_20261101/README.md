# Owned-session notifier close prototype: r549

One fixed-order Linux run with a spawned Fake X owner tested three cases. The
normal close test observed the child exit and parent notifier fd close; an
injected notifier close exception produced unverified UNKNOWN cleanup. In the
third case the fixture stopped `Process.start()` after spawning but before the
parent registered the process; close ran in that window, then the gate opened.
The owner was live after close, and the test failed. Overall exit was 1. The raw
log does not retain the close response or child PID; it supports the observed
post-close liveness, not an independent claim about the close response.

The added close wrapper was subsequently removed from the draft: independent
review identified the startup registration race, unsynchronized cancellation
and concurrent closes, exception paths skipping cleanup, and lack of child or
in-flight descriptor custody. The wrapper's exact pre-run diff remains in the
archive for interpretation. The tests use synthetic Fake X and injected gates;
they do not prove input release, X-server queue drainage, natural failure rates,
MAP01 or general real-time bounds. A running child's test cleanup is attempted;
the fixture does not independently prove every partial-start failure path.

`raw.zip` SHA-256
`06471497217ff59734a25867a3ac0da01cc382a2ab8686564684077d843ac786`
contains conditions, base, pre-run diff, status, stdout and exit; member CRCs
passed. Image digest and Docker flags are recorded conditions, not independently
attested by the unittest output. Do not treat the removed wrapper as a fix.
