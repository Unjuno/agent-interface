# V39 cancellation failure custody: local/Fake X checks

Current V39 `cancel_invalidated_action` waited for `input_released` before
terminal closure. Its wait could consume a matching failed terminal or
`input_release_unverified`, then continue waiting for a success that would not
arrive. The #8954 Executor fence did not repair that outer wait.

The first RED on base `4215f75112c406fa4c6d57c8b7768c4f7ca6e4e0` plus the initial
test addition is retained. One first fixture used the future `failure_root`
argument before implementation, so its TypeError did not establish the terminal
discard. The corrected fixture removes that argument and separately reproduces
failed-terminal/unverified-release consumption; both RED logs remain. This is
ordinary regression development, not a formal/live allocation or no-retry run.

## Behavior and verification

The helper now consumes matching cancellation ACK, verified/unverified release
and terminal boundaries. It retains an early release until the ACK can validate
it; it never silently discards a matching terminal. Healthy success still requires
the existing RunningActionGuardV3 token, clocks, empty-state and cancelled-terminal
checks. Duplicate/malformed/unmatched boundaries fail rather than manufacture
successful release or new input authority. Other program IDs cannot replace the
current boundary.

On send/wait/validation failure, `CancellationReleaseFailed.receipt` returns a
copy containing phase, reason, original matching events, guard state and unknown
physical/task state. The actual main call supplies `args.out`; an exclusive
`running-cancel-release-failure.json` is written before raising. Existing evidence
is not overwritten. A secondary receipt-save failure is attached to the primary
failure. This is best-effort local persistence, not a power-loss durability claim.

Eight test methods cover healthy and early-release ordering, failed terminal,
unverified release, unrelated IDs, nine invalid boundary cases, send failure,
save collision and the composed native-I/O case. The latter uses actual capture,
selected backend, Executor, V4/V12 and RunningActionGuardV3. Semantic compilation
and a health invalidation are synthetic fixtures. Source binding and timestamps
come from fake-client capture; the actual Executor token/attestation is admitted
to the guard. A direct cancellation stream and JSON-cloned event queue emulate
the message boundary; no separate session process or real IPC is qualified.

While the fake KeyRelease send remains blocked, keycode 38 remains down. The
Executor's existing request timeout yields a failed/unverified terminal with its
retained obligation. V39 classifies it as `terminal_without_release`, saves that
exact receipt, and grants no authority without waiting for a fictitious successful
release. The JSON row in each composed-test log retains the held key and
`native_resumed=false` alongside the complete failure receipt. The harness later
resumes its own fake primitive for cleanup; that is not task recovery.

Clean checked source `900a5e639e746de99e70316fcddcc2e067b417e2`: isolated local
runner, 38 modules / 284 methods in normal and optimized Python, zero failures,
one deliberate real-Codex handshake skip (283 executed). This includes the 25
existing running-guard methods. Bounded read-only review independently verifies
the 8 focused methods in both modes and finds no actionable issue.
`normal/` and `optimized/` retain every log and source/status summary.

Commands use `../check_map01_control_regressions.py --output-dir <fresh path>`,
adding `--optimized` for the second mode. Host: Windows, Python 3.13.14,
python-xlib 0.33, Pillow 12.2.0, MCP 1.30.0, openpyxl 3.1.5. `MANIFEST.json`
hashes retained files. No live GUI/display/game/container/model/WSLc allocation
was launched, and no historical producer or consumed experiment was rerun.

## Remaining gates

This is failure classification and custody for V39's active-action cancellation
path. It does not bound cancel write/flush, file I/O, absent-event waits, native
send/sync/readback, scheduler/GIL delay or physical release. Absent events retain
the existing caller wait policy. Cover cancellation and other caller paths need
their own qualification. The failure unwinds to existing controller teardown;
that teardown is not a verified input-release or replacement-session handoff.

No automatic retry, model action reuse or successful recovery is inferred. Window
incarnation, atomic server acceptance, real-process transport, independent task
effect, finite task recovery and matched efficiency remain open in #17/#59.
