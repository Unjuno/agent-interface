# Xvfb late-press recovery and custody follow-up — results

## Execution

All eight frozen attempts ran once in order against the cached Docker image
`sha256:bd191d30ea94871a1d3ca717252cd07a276e8ef7d1bcb4a130b63935ce075425`,
with network disabled, read-only source, private tmpfs, and a dedicated output
mount. The instrumented test source was frozen at
`6c049f504b8d0643fb946c4798e8bc3226218f38`; the preregistration and runner at
`838dd9f0e01af50238d6f4dc1245b730ca856a02`. The container lacked `git`, so the
runtime metadata command emitted a nonfatal `git: command not found`; host-side
commit identities above are authoritative. All reports, publisher traces,
Xvfb processes and final fixture cleanup were retained.

## Results

| Delay | Route | Trials | Immediate readback | Horizon readback | Old-task effect count | Fresh-task oracle |
|---:|---|---:|---|---|---:|---|
| 100 ms | Standard | 2 | `a` up, `b` down | `a` up, `b` down | 2 in both (expected 1) | FAIL in both |
| 100 ms | Prestarted | 2 | `a` up, `b` down | `a` up, `b` down | 2 in both (expected 1) | FAIL in both |
| 250 ms | Standard | 2 | `a` up, `b` down | `a` up, `b` down | 2 in both (expected 1) | FAIL in both |
| 250 ms | Prestarted | 2 | `a` up, `b` down | `a` up, `b` down | 2 in both (expected 1) | FAIL in both |

The independent fresh task still produced its requested property `[3]`, but its
full oracle failed because the delayed `b` press affected the new task window,
the effect count was not exact in several cells, and `b` remained down at the
horizon. For A100/A100r/B100/B100r and one B250 replicate, a delayed old `b`
KeyPress occurred after the fresh session began. The standard 250 ms replicates
and one prestarted 250 ms replicate had exact fresh-task effect counts, but
still failed the full oracle because `b` remained held. Explicit fixture
cleanup restored all keys to up after these scored observations.

Every runtime cancellation remained `UNKNOWN`, with release unconfirmed,
`task_success=null`, late server requests possible, and replay denied. A
readback-verified one-shot supervisor release did not establish a safe horizon.

## Custody publisher trace

All eight child traces recorded the same state progression: initial empty map,
`a` published as keycode 38 before its XTEST press, then the map cleared while
the delayed XTEST request was outstanding, followed by an empty publish. The
`a` press and its queued release are part of the test's real key-chord tap. The
test then injects a delayed `b` press directly through the XTEST library, after
the runtime's tracked tap path; this injected key is intentionally absent from
the runtime's cleanup-obligation set. The parent's empty post-retirement ledger
is consistent with the child's later `a` release publication, not evidence
that the prepress publisher lost `a`.

This resolves the apparent ledger contradiction from the preceding sweep. It
also narrows the counterexample: the fixture's out-of-band late `b` request
demonstrates that the prestarted supervisor's earlier all-up readback does not
exclude a later same-server side effect. It does not show that the public
runtime itself submitted that `b` request or that its obligation ledger
omitted a runtime-owned key.

## Interpretation and limits

The 100/250 ms cells demonstrate that an early cleanup readback is not a
late-request horizon: each injected old-client request arrived afterward,
remained held at the horizon, and made the independent old-task oracle fail.
These are bounded synthetic counterexamples; the harness injects a request
outside the public runtime's input ledger. It does not establish a maximum
production delay, a general X11 failure rate, or the behavior of a live GUI.
The correct next comparison is a tracked same-key delayed request, followed by
a cleanup-only release after its bounded horizon. No WSLc, MAP01, provider cost,
or project-completion claim is made.

Raw JSON, publisher JSONL, screenshots, stdout/stderr, exit codes, Xvfb logs,
and dependency/setup metadata are in `raw/trials/`; `SHA256SUMS.json` binds the
packet. No existing frozen trial was replayed or overwritten.

