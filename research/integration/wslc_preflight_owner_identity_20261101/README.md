# Preflight owner identity on a preconnected supervisor

This follows `wslc_pinned_supervisor_20261101`. The previous candidate kept
one X connection after supervisor startup, but did not prove that it connected
to the original owner before readiness. This experiment injected retirement of
the original private Xvfb after the guarded owner had started but immediately
before the supervisor connected. A second Xvfb reused `:0`, and an independent
target held `b` on the replacement.

| Candidate / condition | Supervisor ready | Fresh `b` after attempt |
| --- | --- | --- |
| Previous candidate, old authority retained | No; authentication rejected | Down |
| Previous candidate, old authority overwritten with new authority | Yes | Up; target observed release |
| Preflight candidate, old authority retained | No | Down |
| Preflight candidate, old authority overwritten with new authority | No; owner identity mismatch | Down |

For the prior candidate's ready case, the harness retired the old owner and
submitted a **synthetic** old `b` obligation to its supervisor. The release
receipt remained `cleanup_status=UNKNOWN` and `release_confirmed=false`. The
target observed a real release on the replacement. No supervisor cleanup was
submitted in the startup-rejected cases; the fixture released the held `b`.

The preflight candidate requires the preconnected supervisor to query the
owner's resource base and exact PID on that same connection before reporting
readiness. It fails closed if the owner identity is unavailable or mismatched.
The owner must therefore have usable XRes process identity in the explicit
authority/default-worker configuration; this is an intentional restriction
that requires compatibility review. The parent continues to bound startup and
retire a failed supervisor. A single same-display trial also exercised real
guarded `a` input, injected owner pause, X server stop/resume, actual cancellation,
independently observed target release, and a fresh successful guarded task.
Cleanup remained UNKNOWN and replay disallowed.

Offline WSLc regression: 62 existing supervisor and owned-process tests passed.
These are single trials and a fixed-order comparison with injected faults, not
a rate, performance result, or proof of every possible server identity race.
XRes is an observation on a connection, not an intrinsic cryptographic identity
of the X server. The experiment does not prove ownership before the guarded
owner's own connection, prevent another client in the same server from sending
input, prove queue drainage, or integrate display retirement into production.
Custom cleanup workers remain unpinned. The draft is not ready to promote on
this evidence alone.

`raw.zip` preserves arm conditions, trial outputs, target events, guarded
artifacts and regression results. Source manifests and harnesses are alongside
it. Private authority files and private launcher commands are excluded; all
nine test cookie records were scanned in raw and hexadecimal form against
packaged material. The Linux memory limit did not include swap enforcement.
