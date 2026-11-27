# Xvfb cancellation release/autorepeat frontier — results

## Execution and custody

All 12 frozen attempts ran once in order against the cached Docker image
`sha256:bd191d30ea94871a1d3ca717252cd07a276e8ef7d1bcb4a130b63935ce075425`,
with network disabled, read-only source, private tmpfs, and a dedicated output
mount. The test-source commit was `806169d7653b8b0228a548d5013ed2ee9a47637f`;
the preregistered runner/design commit was `a59216ecd6d66c1a9e9ec536827445dac92fe74e`.
The container lacks `git`; its metadata capture printed that error but did not
affect test execution. Host-side commit identities above are authoritative.

One runner setup attempt stopped before dependency preflight because the
designated output directory already contained the image-ID receipt. No Xvfb or
input trial started. That setup failure is retained at
`raw/pretrial-output-directory-check.txt`; the scored output was moved to the
separate empty `raw/trials/` directory without changing the frozen conditions.

## Outcomes

| Trial | Delay | Route | Test exit | Independent release readback | Old-task oracle | Final fixture cleanup |
|---|---:|---|---:|---|---|---|
| A100 | 100 ms | Standard | 1 | `a` up, `b` down | Not reached; assertion stopped before horizon | All keys up |
| B100 | 100 ms | Prestarted | 1 | `a` up, `b` down | Not reached; assertion stopped before horizon | All keys up |
| B250 | 250 ms | Prestarted | 1 | `a` up, `b` down | Not reached; assertion stopped before horizon | All keys up |
| A250 | 250 ms | Standard | 1 | `a` up, `b` down | Not reached; assertion stopped before horizon | All keys up |
| A500 | 500 ms | Standard | 0 | Both up | PASS, exact effect count 1 | All keys up |
| B500 | 500 ms | Prestarted | 0 | Both up | PASS, exact effect count 1 | All keys up |
| B500r | 500 ms | Prestarted | 0 | Both up | PASS, exact effect count 1 | All keys up |
| A500r | 500 ms | Standard | 0 | Both up | FAIL, effect count 2 (expected 1) | All keys up |
| A250r | 250 ms | Standard | 1 | `a` up, `b` down | Not reached; assertion stopped before horizon | All keys up |
| B250r | 250 ms | Prestarted | 1 | `a` up, `b` down | Not reached; assertion stopped before horizon | All keys up |
| B100r | 100 ms | Prestarted | 1 | `a` up, `b` down | Not reached; assertion stopped before horizon | All keys up |
| A100r | 100 ms | Standard | 1 | `a` up, `b` down | Not reached; assertion stopped before horizon | All keys up |

All 12 runtime cancellation receipts kept `cleanup_status=UNKNOWN`,
`release_confirmed=false`, `task_success=null`,
`late_server_request_possible=true`, and `replay_allowed=false`. On the
100/250 ms cells, prestarted cleanup's separate release receipt could be
readback-verified, but the later injected `b` press still left `b` down. This
does not upgrade or contradict the conservative runtime receipt.

The first four 100/250 ms attempts failed their immediate independent keymap
assertion and therefore did not reach the horizon or independent task oracle.
Their later all-up state is explicit fixture cleanup after the scored
observation, not recovery evidence.

## Interpretation

The observed exact-effect boundary varies with the injected request timing in
this fixture. At 500 ms, both B replicates reached one effect; A had one
one-effect result and one duplicate-effect result. At 100/250 ms, both routes
left a delayed `b` press down at the immediate readback. These small counts do
not establish a causal effect size, general reliability, or a universal
autorepeat threshold. The fail-closed outcome and `UNKNOWN` custody remain
correctly reported.

The new 100/250 ms observations show a useful limit of a single early release
attempt: it can verify neutral input at that instant yet an already-queued
request can act afterward. The next probe must continue through the horizon and
separate tracked same-key late input from fixture-injected unrelated-key input.

## Evidence and limits

Raw JSON, screenshots, publisher-independent logs, Xvfb logs, attempt exits,
setup evidence, and run metadata are under `raw/`; `SHA256SUMS.json` binds all
raw files. These trials are synthetic Xvfb only. They are not WSLc, a live GUI,
MAP01, a provider/model efficiency comparison, a production crash test, or
project completion evidence.
