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

## Follow-up run 39157339388 — 2026-10-19

The follow-up at PR head `85dfeae0bfcb398f05c4b519ce515a29c4254038` extended
the owner delay to 8,000 ms. The child was terminated about 151.8 ms after
flush. XRes still reported `still_connected` at roughly 1.0 s, 5.0 s, and
after the delayed-event horizon (the final query was about 1.0 s after that
horizon). The keymap was up before cleanup, after the independent
KeyRelease+XSync, and after the delay horizon; `late_input_observed` was false.
The post-horizon query therefore did not represent a post-disconnect readback:
the owner remained present in XRes. The final cleanup also read both keys up.

This run did **not** reproduce a late keypress and did not meet the expected
XRes-disappearance bound. It cannot show that an 8-second delayed request would
execute after disconnect, because disconnect was never observed. It also does
not establish a cleanup fence or general Xorg behavior. The follow-up CI
artifact is [`raw/run-39157339388.json`](raw/run-39157339388.json), SHA-256
`3d129b96ed910c28bac683422847b5802d788045404633432b8e8037fba8d4e3`.
The integration test fails on its explicit candidate-late-press assertion;
the other recorded PR checks pass. Keep this as a distinct bounded negative
result, preserve release as `UNKNOWN`, and leave Issue #17 open.

## Follow-up run 39157580185 — observation-only assertion

After the test was changed to accept either measured key state instead of asserting the hypothesized late press, the dedicated Xvfb job passed at PR head `4ffa711d6bf4a5e60f18109dc779ed753eff4f88`. This run used X.Org release `12101011`, XRes `1.2`, XTEST `2.2`, and an 8,000 ms delayed request. The owner was terminated 151.1 ms after flush. Independent XRes probes at about 1.0 s, 5.0 s, and after the delay horizon (about 9.5 s after kill) all reported `still_connected`. Both keys were up before cleanup, after the separate KeyRelease+XSync, and after the delay horizon; `late_input_observed=false`. Final cleanup also read both keys up.

This is a successful measurement procedure with a negative late-input observation for this bounded private-Xvfb run. It does not observe a state after XRes disappearance, and therefore cannot establish whether the delayed request would execute after actual client disappearance. It is not a release fence, standard-caller result, physical desktop result, or general Xorg teardown claim. The test now records either late-input outcome without making one outcome a test-pass prerequisite. Raw artifact: [`raw/run-39157580185.json`](raw/run-39157580185.json), SHA-256 `b923d0e44ff05800d7b3fb265f89becb1e4af7b3e431dd24e2f534a62d04bc4f`.

## Integration status

PR #9057 was squash-merged at `6d91411cf8b90d514ac0d05a68009e6667113d7e` after the observation-only Xvfb test and all reported checks passed. The merge integrates the bounded measurement harness, not a release-fence guarantee. This packet separately retains the earlier test-assertion failure and the later procedure pass; neither observed XRes disappearance or proves post-disconnect ordering.

## Extended post-horizon run 39158398302 — 2026-10-19

PR [#9062](https://github.com/Unjuno/agent-interface/pull/9062) extended the supervised XRes poll after the 8,000 ms delayed-event horizon from 1 s to 10 s. The private-Xvfb job passed at head `d3dd3152206d107166c376ce13eb6d7191b9260e` and the PR merged at `2471afbaf96481fcc29c16328cbc44232c85bbc3`. On the same X.Org release `12101011`, the delayed request owner exited with `-15` about 151.5 ms after flush. XRes still reported `still_connected` after the horizon, with the 10 s post-horizon probe completing 18,511.3 ms after owner termination. The keymap after the extended probe remained `a=false, b=false`; `late_input_observed_after_extended_probe=false`. No client disappearance was observed, so `key_down_after_disconnect` remained null.

The untouched CI artifact is [`raw/run-39158398302.json`](raw/run-39158398302.json), SHA-256 `767c1d48de54d1d9388c156c2898622c7111522d39e0985790fe29351a803323`. This strengthens only the bounded Xvfb observation: the owner remained present in XRes longer than the scheduled delay plus 10 s. It does not establish what happens after XRes disappearance, an input-release fence, standard-caller integration, physical effects, or a general X.Org deadline. Preserve release as `UNKNOWN`; no WSLc allocation was used.
