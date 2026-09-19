# MAP01 deterministic invalidation controller v27

V26's first live run did not encounter a health-ROI change, leaving the final
controller-level cancellation composition unexposed.  V27 adds an explicit,
opt-in integration-test hook without changing the natural visual guard or the
normal command.

The hook selects one iteration and fires once after a fixed number of exact
observations have passed through the real game queue.  The natural visual guard
evaluates first and always has priority.  The injected record is labelled
`INJECTED_INVALIDATION`, claims no semantic visual change or task success, and
can only reduce existing authority.  It cannot authorize an action.

The resulting controller path is the same path used by a natural invalidation:
mark the matching planner turn stale, send one typed interrupt, cancel the
current cover, await both terminal events, record the ineligible planner result,
and continue from a fresh observation.  A discarded result with `action: null`
cannot supply the next iteration's cover, which compiles to bounded coast.

Five injector/v27 tests cover one-shot selection, natural-event priority,
nonadvancing-sequence refusal, invalid configuration, and discarded-cover
inheritance.  Existing adapter and controller suites remain green.  The hook is
absent unless both command-line injection arguments are supplied.

The next frozen allocation needs only two decisions: inject decision zero after
four exact observations, then require the interrupted thread to accept a fresh
decision one.  This is a construction test rather than a gameplay benchmark.
After it passes or fails once, return to the hook-free v26/v27 normal condition.
