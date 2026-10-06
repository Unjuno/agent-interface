# Per-key owner source guard

The combined V15/per-key startup selects a different owner file from the requested archived A01 owner because Python has already cached the current owner. This repair rejects that mismatch before `sources.json` is written or a Session is constructed. It checks the class used by the selected backend constructor, rather than the common module name.

The production delta is eight added lines in `research/doom/session_map01_v12.py`, relative to PR #8065 head `4158d9b063e7cbf56828f1b0667ec2714af0ff2b`. The regression runs actual V12/V15 startup imports in four fresh Python processes, with inert Xlib/vizdoom modules and blocked native/process/thread construction. The selected positive routes are intercepted at the Session constructor boundary.

| Route | Before guard, red-v2 | With guard, green-v2 |
|---|---|---|
| Clean V12 + per-key | Requested A01 owner selected | Requested A01 owner selected |
| V12 + current owner pre-cached + per-key | Wrong current owner selected | Explicit rejection before manifest/session |
| V15 default | Current V4 release-batch owner selected | Current V4 release-batch owner selected |
| V15 + per-key | Wrong current owner selected | Explicit rejection before manifest/session |

The first exercised regression has two failures and two passing controls. The first patched regression passes 4/4. Both use the identical test source. No native input, owner thread, X server, game, model, container or formal allocation ran. Candidate tests were run on Python 3.12.14, macOS 27.0.1 arm64. No performance inference is made from test duration.

`construction-note.md` retains the two harness/edit mistakes: red-v1 started before source export finished (no test executed), and green-v1 ran unchanged source after the first edit assertion failed. Neither is mislabeled as a successful patched run. Their complete test-command stdout/stderr and runner exit receipts are retained; the edit assertion itself was only captured in tool output.

This is a fail-closed mitigation, not full V15/A01 integration. Combined mode remains unsupported in the exercised fresh startup. A compatible measurement adapter must preserve current batch order and release-pending guards and establish actual per-key receipt emission separately. This check identifies a source-path mismatch; it is not a general attestation of code modified in place after import. It does not prove owner execution, physical release, useful task effect, live threat reaction, recovery, or MAP01 completion.

Source reconstruction uses the exact parent Git commit plus the committed production/test delta. `base-source-manifest.json` pins the 56 production source files used by the exported startup closure; per-run `sources.json` pins all 57 files including the test. `source/` contains inert snapshots of the changed production source before/after and the unchanged regression. The older three-route counterexample and its full original closure remain in PR #8079; it has not been rerun or overwritten.

Publication is a draft stacked on #8065, not a main integration. FINAL-v5 nonauthor content quorum and exact current-tree integration have not been satisfied. Independent raw review is a technical audit, not a quorum vote.

The existing nonauthor agent's final raw-only audit v4 passes: it checks route outcomes, receipt hashes, all 56 base source pins, all 57 patched-export pins and the limited production/test delta. No candidate was rerun for the audit. Versions v1 and v3 fail due to auditor comparison mistakes (elapsed test duration equality and comparison of baseline hashes against the later patched export); v2 and v4 pass. All scripts, results and `independent-audit/audit-corrections.md` are preserved. The first audit was not a PASS.
