# Matched one-second late-ACK Xvfb comparison — results

## Execution

The four preregistered attempts ran once, in ABBA order, in the cached Docker
image pinned in `README.md`. Docker used `--network none`, a read-only source
mount, and a private tmpfs. No model, provider, WSLc, physical desktop, or game
was used. The runner completed all four attempts. Raw JSON, images, logs,
exit codes, setup records, and environment metadata are retained in `raw/`;
`SHA256SUMS` binds each retained raw file.

## Outcomes

| Trial | Arm | Test process | Old-task independent oracle | Runtime custody/release | Fresh-session task |
|---|---|---|---|---|---|
| A1 | Standard caller | FAIL (exit 1); assertion expected a `readback_verified` runtime release receipt but observed `unknown` | Not reached; no independent task-oracle result | UNKNOWN; final cleanup keymap was all-up | Not reached |
| B1 | Prestarted supervisor | PASS (exit 0) | PASS, exact effect `[1]`, count 1; release and late horizon keymaps all-up | Runtime receipt remains UNKNOWN; separate parent-client release readback verified | PASS, exact effect `[3]`, count 1; no late old keypress observed |
| B2 | Prestarted supervisor | PASS (exit 0) | PASS, exact effect `[1]`, count 1; release and late horizon keymaps all-up | Runtime receipt remains UNKNOWN; separate parent-client release readback verified | PASS, exact effect `[3]`, count 1; no late old keypress observed |
| A2 | Standard caller | PASS (exit 0) | FAIL: final effect value `[1]`, but independent effect count was 6 (expected 1); keymaps all-up at release and horizon | Runtime receipt UNKNOWN; separate parent-client release readback verified | PASS, exact effect `[3]`, count 1; no late old keypress observed |

Cancel response latency was 258.964 ms (A1), 258.141 ms (B1), 260.209 ms
(B2), and 259.425 ms (A2), all below the frozen 3,000 ms bound. Where a
separate release timestamp was retained, cancel-start to verified release
readback was 366.608 ms (B1), 364.827 ms (B2), and 848.311 ms (A2). A1 did not
retain an independent release timestamp. These are four observations, not a
reliability or general speed estimate. Fresh-task input-to-effect-readback was
47.931 ms (B1), 54.752 ms (B2), and 42.677 ms (A2).

A2's saved application event sequence shows the initial `a` KeyPress, then five
X server autorepeat KeyPress events at roughly 40 ms intervals before the
corresponding releases. The independent effect count therefore reached 6,
while the final semantic property remained `[1]`. The delayed old `b` press was
not observed and keys were up at the horizon. This makes a held-key repeat
during the standard caller's release delay a concrete explanation for the
count mismatch in A2; it does not explain A1's earlier receipt assertion.
A1's failed assertion is retained as a failure, not converted to an oracle
pass. Its final keymap observation does not repair the missing independent task
oracle or runtime custody receipt.

## Interpretation

For this small synthetic fixture, both prestarted trials passed the old-task
effect oracle; the standard-caller arm had one assertion failure before that
oracle and one exact-effect-multiplicity failure. This is a useful signal for
the prestarted path and a concrete standard-caller defect candidate, but n=2
per arm is exploratory and does not establish a general causal or reliability
claim. The independent keymap and application oracles do not change the
runtime's UNKNOWN cleanup/custody result. No trial establishes live GUI,
Win32, WSLc, MAP01, provider-cost, or broad efficiency behavior.

The immediate engineering target is to reconcile standard-caller cancellation
withheld-ACK cleanup and the exact-effect multiplicity oracle while preserving
UNKNOWN whenever runtime custody is unconfirmed. Do not treat the B-arm result
as permission to weaken the runtime receipt contract.
