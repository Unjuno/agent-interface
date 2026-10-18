# Private Xvfb XRes disconnect-order observation — 2026-10-19

This packet preserves the first CI run of the delayed-XTEST disconnect test in
open [PR #9057](https://github.com/Unjuno/agent-interface/pull/9057), head
`632f7ff737d88090460d503bb5836088bd7a8812`. GitHub Actions run
[39156382299](https://github.com/Unjuno/agent-interface/actions/runs/39156382299)
completed with `x11-integration` failure. It used the workflow's private Xvfb
display `:88`; it was not a WSLc allocation or a physical desktop test.

The report identifies the server vendor as **The X.Org Foundation**, release
number `12101011`, with XRes `1.2` and XTEST `2.2`. The owner queued a 3,000 ms
delayed fake KeyPress of `a` followed by `b`, flushed, and was terminated about
151.7 ms later (process return code `-15`). Independent XRes queries about
1,011.8 ms and 5,012.0 ms after termination both returned `still_connected`;
the recorded time through the second query was about 6,027.4 ms. The test's
expected disconnect-by-5-second bound was therefore not observed.

Both keycodes were up in the initial and approximately 1-second keymap reads.
Because the client did not disappear, the report leaves the post-disconnect
and post-delay keymap observations null and `cleanup_status` as
`not_attempted`. Its `finally` path did complete a separate KeyRelease+XSync;
the final readback reported both keys up. This run therefore observes delayed
XRes client disappearance and successful cleanup of this private Xvfb state,
but it does **not** establish whether the delayed request later executed,
whether the client eventually disconnects, or whether cleanup is a bounded
fence against late input.

The untouched CI artifact is [`raw/x11-disconnect-fence.json`](raw/x11-disconnect-fence.json),
SHA-256 `cdecda8f98ef26a5ae95db812514053a5368158291b38af81e5f78b5598c7eee`.
The exact test source and workflow are at the linked PR head. Do not rerun this
run as if it were an unused WSLc allocation; use a new test revision if the
observation sequence is extended. The next discriminator on the PR branch is
to treat “still connected at 5 s” as a measured outcome, capture key state at
the delayed-event horizon, perform the independent KeyRelease, and read again
after a bounded post-cleanup interval. That distinguishes a delayed event from
client-teardown timing while retaining release as `UNKNOWN`. Keep Issue #17
open.
