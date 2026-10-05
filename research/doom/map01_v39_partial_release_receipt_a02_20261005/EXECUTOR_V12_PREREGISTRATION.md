# ExecutorV12 partial-release composition A01

**H.** The A02 direct owner/bridge result does not show whether a confirmed
per-key UP remains observable when cleanup fails during an actual
ExecutorV12 expiry, nor whether ExecutorV12 can retry the remaining held key
and truthfully report terminal neutrality.

**T.** On frozen PR #7864 head `de9a37d5d0eca2b258982b02f2fb2a401bba293c`,
use the existing fake-display owner and bridge harness with current-main
ExecutorV12 sources. Hold F8 and F9 under separate step contexts. Let the
owner expiry cleanup successfully release F8, inject one exception before
the second `KeyRelease` takes effect, then let ExecutorV12's terminal cleanup
retry the still-held F9. Run once with the exact #7847 pre-fix owner source
(RED), then with the A02 candidate source (GREEN).

**D.** RED must lack the partial owner record and the F8 bridge release
measurement. GREEN requires exactly one explicitly unverified partial owner
record carrying only F8, both confirmed UP receipts before terminal
publication, a single `expired` terminal with verified cleanup after the F9
retry, empty fake physical and bridge-held sets, and a later DOWN rejected
without injection because the owner fault remains sticky.

**C.** This is one deterministic fake-display integration schedule. The
injected failure occurs before F9's release takes effect. It measures
ExecutorV12 terminal cleanup composition and one successful retry; it does
not estimate failure frequency or recovery reliability.

**U.** No real X11/OS input, application consumption, useful feedback,
bounded recovery efficacy, threat exposure, gameplay/MAP01 outcome, latency,
or live allocation is established.
