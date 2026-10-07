# #5260 A02 — descriptive delivery failures, readiness custody STOP

Overall qualification: **STOP_READINESS_CUSTODY_AFTER_PASS_AUDIT**.
The candidate and separate auditor each ran once, exited 0, and retained
all 96 rows; frozen auditor errors are empty. A stronger post-outcome check
then failed readiness epoch binding in all 96 rows. The descriptive delivery
observations below are not promoted to a fully qualified hypothesis PASS/FAIL.

## Formal outcomes

Each row is a fresh app. The table pools the two equivalent coordinate
derivations descriptively; it does not claim independent window-ID treatments.

| Click-to-first-key delay | Idle exact saves | Busy exact saves |
| --- | ---: | ---: |
| 0 ms | 3/16 | 0/16 |
| 50 ms | 16/16 | 14/16 |
| 100 ms | 16/16 | 16/16 |

65/96 saved exactly hxy; 31/96 did not. In all 31 nonexact rows, the initial
h was observed in the decoy Entry. 29 saved xy with decoy h; one saved y
with decoy hx; one saved empty with decoy hxy. All rows clicked Save once.
The full 12-cell (two derivations × three delays × two loads) counts,
ordered app events and clock brackets remain in the raw/audit files.

50 ms did not suffice in 2/32 rows here. The 32/32 exact saves at 100 ms
are a finite observation, not optimality or universal readiness assurance.
No default wait was changed, no missing character was replayed, and no
recovery was attempted. The preformal busy smoke is excluded from these counts.

## Execution and custody

- Source commit c120b70e0ac4b79715d7f031205ea5abb7b1e2f5; base main
  e74cfc78b84d286ff3faabf2696129b988655c1b. GitHub MCP freeze readback
  preceded the Issue registration and formal launch.
- FREEZE SHA256: 468c8c04aca1501c30791071da739058db998a35f467e45161a00e2acb64f763.
- Candidate: 2026-10-03T12:42:33.402172–12:44:51.569246Z; exit0,
  host wall138.1676s. Raw SHA256:
  19258c28c4028b60605d71a5d42a998e1b2532a06ca4b181edf7ce99bbe8e3b7.
- Auditor: 12:45:29.657631–12:46:34.167201Z; exit0, wall64.5092s.
  Stdout SHA256: 25a97b4de4aaa8d1e9cdaac1c54982755ce8f3bd6bcb1a2e67a18821da3d755f.
- One private WSLc image:
  sha256:217851fe68e7340cd6301e6d1a1bd79d2c7b6cb4d13eb444a06fabaf0fde3417;
  Linux amd64, Debian Python3.13.5/Tk8.6, US XKB, Xvfb/Openbox.
- Formal source read-only; auditor candidate input read-only; derived
  images written only to auditor output. Xvfb/Openbox exits0. --rm was
  requested for both containers. Scoped CPU release recorded in #5085.

Both launchers retained the WSL warning: kernel swap-limit capability
unsupported or cgroup unmounted, memory limited without swap. Xvfb logged
non-root creation of /tmp/.X11-unix was unavailable; Openbox logged an
unwritable /nonexistent cache/home, Fontconfig cache and absent menu.
Despite those warnings, the owned Xvfb/Openbox remained alive during input,
all apps completed, and their raw/cleanup records are retained. We do not
rewrite warnings, assert effective limits, or generalize host resource safety.

## Independent validation and limits

The first retained cross-file verifier exited1: all96 ready_binding errors.
The runner's first ready snapshot (preserved inside raw) is not the final
ready.json. Geometry, baseline image hash and Map/Configure-event list
agree96/96, but final ready_ns is later96/96, after click95/96 and after
first key48/96; final app/ready identities agree96/96. Source tracing finds
maybe_ready calls update_idletasks before setting ready_written; reentrant
callbacks can enqueue multiple finalize_ready/focus callbacks. This means
the intended stable readiness epoch/control is not qualified.

The first failing checker source, its input manifest, original RUN descriptor
and exact failed stdout/stderr/receipt are retained under
results/readiness-qualification-first. The delivery verifier now recognizes
ONLY this exact96-error STOP as correctly preserved negative evidence;
any additional/missing custody error fails packaging. A packaging PASS
never clears the scientific STOP. No original source/raw/audit was repaired.

The frozen auditor independently reconstructs schedule/cardinality,
mapped geometry/coordinate derivation, delay minimum, worker coverage of
key dispatch, image hashes/byte counts and source/fixture bindings. It
accepts delivery failure as an outcome, not an audit error. Baseline
integrity96/96; first XWD frames96/96. OCR exact-target matches0/96: OCR
is exploratory/unresolved, not evidence of visual success or useful feedback.

The additive retained verifier cross-binds every app_result, first_visual
and stdout record, checks96 distinct app PIDs/receipts, retains the96
readiness mismatches, and rejects15 raw corruption copies without a
GUI/container or original-raw edit. Custody/unsafe manifest and exact STOP
preservation are unit-tested. Formal source/tests are not repaired after outcome.

This task records missing-first-character observations in a disposable
Linux Tk fixture with explicit decoy focus and an unqualified readiness epoch.
It does not independently establish that this mechanism caused the original
integration failure. It does not replay
the original Agent Interface integration, isolate WM/Tk causality, establish
native Windows behavior, classify genuinely useful visual feedback, compare
Docker with WSLc, or prove memory/iteration benefit. The two coordinate
formulas describe the same root pointer point, not two addressed-window APIs.
Image capture itself can delay app event handling; the same instrumentation
is used across cells, and its clocks are retained, but this is still a limit.

#5260 and #5296 remain open for genuinely matched integration/readiness
qualification. Old r0 STOP and A01 HOLD_NOT_AUTHORIZED remain unchanged.
Next experiment should test an explicitly observed target-focus/readiness
barrier in a fresh allocation and then the real public client path, not
silently lengthen the production wait or replay these consumed rows.
