# Selected backend owns the external input service

Continue#59 /#8998: add an explicit `owner_service` keyword to the existing
process-identity Backend, without replacing the default local mode. An
OwnedOwnerAdapter owns ordinary RPC, cancellation client and exact service
handle, exposes owner_id/append-only records/call/close, installs the original
lease watcher before input, and keeps the first unresolved obligation forever.
Backend/Executor existing custody rejects new work or replacement after it.
Later service exit or release cannot upgrade first failed control/close results.

Current constructors replace empty owners at four layers. When an external owner
is explicitly selected, each must reuse the same provided adapter without
constructing any local input owner; local mode preserves all original replacement
behavior. Capture/process identity readers remain parent-side. Reject window
lifecycle transfer and unsupported pointer programs before any input. Support
bounded read-only `surface_context` over ordinary RPC for the actual inherited
binding/capture path (explicit non-root XID, no lease, validated geometry); it
does not confer input authority. New input always retains original capture source.

Tests use a realistic Fake parent window tree and Fake child geometry, rather
than patching backend.binding. Parent native display construction is forbidden
in the external mode. Exercise normal actual Executor, worker-paused cancellation,
ordinary reply in flight, blocked release first-control failure followed by late
successful cleanup, new Executor rejection, remote generation mismatch and
backend source binding. Validate pointer/window rejection and all resources joined.
Pure tests cover partial adapter startup and error/close result retention.

Preserve reds/first sources/raw/conditions, selected regression normal/-O, frozen
loaded sources and offline saved audit with altered negatives. Bounded review,
permission/protection check and verified main integration complete this step.
No real display/input, WSL/container, model/game, physical release-time or task
effect qualification. The next boundary is production session/controller selection
and death cleanup, then live native/app qualification under current permission.
