# Explicit recovery with an optional post-release image

The prior [primary recovery trial](../input-recovery-primary-01/README.md)
needed a separate observation call after input recovery. The new optional
`interface_recover_input(current_binding_revision=1, target="counter",
region=[0,0,560,260])` captures the selected window after verified release.
It does not choose or replay input. Release-only behavior remains available.

## Fresh primary trial, 2026-09-28

The primary assistant used the same known counter app and injected-fault wrapper
on a fresh private Xvfb/Openbox session, with autorepeat disabled. The first W
press was processed but its acknowledgement failed; first cleanup deliberately
omitted release. Recovery returned verified empty input, revision 2, and a native
image showing Count 1. The assistant reviewed that image, authored one remaining
W pulse, reviewed Count 2, saved with S once, and reviewed Saved Count 2.
Only after closing the connection were saved.json and application events read.
They showed count 2 and exactly W/count1, W/count2, S/count2.

Six MCP calls were used, compared with seven in the preceding construction:
observe, failed input, recover-with-image, remaining increment with image,
save with image, close. This eliminates one explicit observation request in this
case. Both trials delivered four images. No claim of lower model tokens, cost,
matched end-to-end latency, useful-feedback onset or human tempo follows.
These are sequential source-known constructions, not randomized benchmarks.

Runtime source: `6c34107a22af77e3f30f9c1db24ccba307721571`.
Exercised archive SHA-256:
`7962f327fad5d9ca63273c059e23c98186cdc7713766431f6d0418e97c987591`.
The archive and build metadata, app/fixture/relay/fault sources, all requests,
replies, screenshots, five reply-bound primary review notes, host event times,
saved output, app event journal and cleanup are retained in raw.tar.gz.
The relay exited 0. Owned Xvfb/Openbox/app processes were reaped with 0/1/-15;
the app was terminated during fixture cleanup after saving, not normally exited.

The observations and leases remain caller assertions: source sequence is not a
server-issued freshness token and prior relay return +120s is an admission
expiry, not a hard watchdog. The later input programs retained explicit 20ms
holds and 100ms pre-capture waits. No new default wait, retry, sensor or model
was introduced. The recovery capture itself adds no wait for application redraw.

## Failure behavior and validation

Invalid region syntax, partial target/region pairs and unknown targets refuse
before release. Failed recovery never captures. Successful release commits its
new revision before capture; a vanished window or capture exception retains that
success plus observation failure. Caller must observe separately when no usable
image is returned, never repeat recovery merely because capture failed.
Historical reads never repeat release or capture. The image is not a semantic
completion check, and a current capture can still contain unpainted app state.

Local native checks passed 272 protocol +122 harness/distribution tests. New
controls cover malformed capture requests, no capture after failed release,
capture failure preserving revision, stale refusal, request-persistence failure,
and historical retrieval without recapture. Logs are included. An initial
post-test command looked for nonexistent summary.json; the actual result.json
reported PASS and is retained. No test or GUI trial was restarted for that typo.

Run `python3 -O runtime/results/recovery-capture-primary-01/verify.py`.
The verifier checks bytes, request/reply/session identities, post-release capture
ordering, image delivery, saved effects and cleanup. It does not interpret pixels
or independently prove the review notes' semantic content. Prior frozen evidence
is unchanged. Further ordinary-app and matched performance validation remains open.
