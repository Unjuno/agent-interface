# Fake X queued-DOWN cancellation through the guarded MCP caller

**Disposition: `LOCAL_CALLER_CONSTRUCTION_PASS` (scoped).** This is a deterministic
caller regression/construction, not a formal WSLc allocation. It does not consume
or renew `fake-x-release-order-a01-20261018` or any other allocation.

## Question and method

Parent question: [Issue #17](https://github.com/Unjuno/agent-interface/issues/17).
The prior A01 model showed that an independent UP connection can produce a false
empty readback while the original writer can still deliver a late DOWN. This
construction connects the queued-before-server-processing schedule to the
current guarded MCP caller with one session connection.

The test inserts a Fake X queue between the real backend/caller code and the
synthetic server bitmap. It queues CTRL DOWN, blocks the same connection at
`sync`, requests and repeats cancellation, and observes the public call and
session before resuming the server. The pre-resume assertions require:

- CTRL remains in the backend ownership ledger while the Fake X keymap is empty;
- the response and result lookup remain `pending`, with no release confirmation;
- new input, close and recovery remain `busy`;
- the queued DOWN belongs to the session's sole writer.

On resume, the Fake X server applies DOWN before the caller's cleanup UP on that
same connection. Cancellation prevents the remaining chord key from being sent;
the call ends `execution_failed` with verified Fake X cleanup, and replay of the
old call is refused. This preserves the observed event order, not an X server
cross-connection ordering guarantee.

## Result and limits

The selected caller did not treat an empty bitmap as proof of release while the
writer was blocked. It retained custody, waited for the original writer to
resume, then verified the same-writer cleanup and rejected suffix/replay. The
five-second gate is only a harness escape; no release-time threshold was tested.
There is no actual X server, GUI, native/physical input, application effect,
MAP01 task outcome, independent success oracle, latency or efficiency result.
The Fake X pass does not prove bounded physical release when the server or native
writer never resumes.

**WSLc boundary:** standard Ubuntu 24.04.3 on WSL2, kernel
`6.18.54.1-microsoft-standard-WSL2`, Python 3.12.3 was used only for local
regression tests. No WSLc CLI, image/container listing or lifecycle command was
run. The scoped WSLc client ownership record in [Issue #7924](https://github.com/Unjuno/agent-interface/issues/7924)
remains `UNKNOWN`; this test is not evidence that its shared lane or any formal
WSLc allocation is available.

## Reproduction and retained output

After main advanced to `7265babbbf04af4b65c3ac6fb67e0dfd8cf7565a`, the
transport-cancellation, wait-budget and process-identity modules were rerun and
passed **29/29** in normal and optimized Python. The exact current-main logs are
[`normal-current-main.txt`](normal-current-main.txt) and
[`optimized-current-main.txt`](optimized-current-main.txt), with SHA-256
`a853c5ee22e865d668aa60f5bbe6ea2efc07142618739f5e998df1e56156b8d9` and
`fdce225793bf5b84053fd633195764bf92395b06fea9a7f8433dd5cef3bf9978`.

At base main `0e5d698b02264a42cc2ef684f64ae13d9ac4ce17`, the transport-cancellation,
wait-budget and process-identity modules passed **29/29** in both normal and
optimized Python. Logs are retained as [`normal.txt`](normal.txt) and
[`optimized.txt`](optimized.txt). The optimized log includes one asyncio
slow-task diagnostic from the stdio test; the suite completed with zero failures.
The changed test module's Git blob ID is
`72b65ccd9afa562d4e4293d3ddca6619e367343f`.

The broader CLI test discovery found 435 tests; 434 passed and one portable
relay packaging test errored before its assertions. In this WSL-on-NTFS checkout,
the copied test root's `.git` file contains a Windows absolute path, which
`/usr/bin/git` interprets as a path beneath the POSIX checkout; the resulting
`rev-parse --verify HEAD^{commit}` fails with “not a git repository.” This is a
test-environment limitation, not counted as a suite pass. The same single
environment error occurred in both normal and optimized full discovery; each
run reported 434/435 passing and is not a full-suite pass. The preserved logs
are [`all-cli-normal.txt`](all-cli-normal.txt) and
[`all-cli-optimized.txt`](all-cli-optimized.txt), with SHA-256
`96945499f78b5d809702165f92678f79a73a4bd41c5ec1300964105b0781df18` and
`4306c12187fe1aa0a9e9c3a3ccf6905e1efcc56b9e9fcc3825c6e82dd2d64c46`.
The selected three-module suite passed 29/29 in both modes; focused log SHA-256
values are `a35bbf5201e135a7ec4b88ac8d2cd5ff18d555f4be4a958530bd37187f456021`
and `96bb403317eabead3b4fd788d21c49fc534c7a5fabd623e204bd90b7f53e9260`.
Earlier incomplete sparse checkout attempts are retained as
[`all-cli-sparse-checkout-attempt.txt`](all-cli-sparse-checkout-attempt.txt) and
[`all-cli-sparse-missing-quartz.txt`](all-cli-sparse-missing-quartz.txt).
