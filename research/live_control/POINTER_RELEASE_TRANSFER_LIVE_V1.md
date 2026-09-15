# Pointer two-phase release transfer v1

The DOOM keyboard result proves early physical-release publication when an
explicit cancel races with artifact work. The next candidate transfers the same
interface to a different input semantic: a real X11 Button1 drag that becomes
invalid because focus moves to a private sink window, without an explicit cancel.

Executor v13 starts one release watcher for every accepted lease. InputOwner v10
can therefore publish `focus_changed`, `surface_changed` or `expired` release in
the same lease-token-bound format as `cancelled`. The worker also checks once
before terminal publication, preserving release-before-terminal ordering if the
watcher and worker race. Normal completion emits no interruption release event.

Synthetic focus/surface/expiry and normal controls pass on Windows and WSL.
One private-Xvfb Inkscape allocation is frozen with the historically exercised
seed212 drag from(618,391) to(638,391), one episode, zero retry/model calls. It
requires observed physical Button1 down, a verified empty `focus_changed` owner
release, exact accepted lease token, release event before a matching
`needs_decision` terminal, only the first drag point admitted and no explicit
cancel. Frozen limits are50ms focus-request→physical-release,75ms to release
publication and150ms to terminal. All25 source hashes and output absence verify
on Windows/WSL. Run once; retain the first failure without retry.
