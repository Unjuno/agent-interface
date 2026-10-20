# PR audit disposition r01 — 2026-10-20

Audit source: `main` at `81819356e42ef7ec21587ffbc0235fc7d8c1fcf4`.
The nine PR states and heads below were reconciled with the retained family
records on 2026-10-20. Live rechecks against `main` `53186c391103d50cb0b7555165a174a15842f586`
and after docs-only PR #9265 at `6e2d1841646ef4a43ee91b043830c3a7b30eabed`
confirmed the same states, head SHAs, and recorded base SHAs for all nine PRs.
The base SHAs are historical and differ from current main. Three completed
read-only audits are preserved below. This is an integration receipt, not
approval to merge, close, rerun, or remove branches/worktrees.

| PR | Live state (head / recorded base) | Preserved finding | Next disposition |
|---|---|---|---|
| [#8702](https://github.com/Unjuno/agent-interface/pull/8702) | Open, Draft; `d2c9fdec7c2d8f4916af68e35dd1350efffe2564` / `74fc81e0a447ad05e4a2220b16d7949979635fb9` | The tracked package checksums and manifest digest are internally consistent, but the private raw manifest/event stream needed to reproduce the A07 claim is unavailable in inspected tracked sources. The retained owner reconciliation does not establish physical key state or task effect. | Keep the unique A07 record on evidence-custody hold; do not rerun the consumed allocation. Resume only if the unchanged raw bundle or a privacy-approved reproducible verification manifest is supplied. See the [A07 custody audit](issue-59-a07-custody-audit-20261019-r01.md) and [#59 family record](../ideas/map01-live-guard-evidence-family.md). |
| [#8832](https://github.com/Unjuno/agent-interface/pull/8832) | Closed; `631b9dfc16f5f682eab72ad1a88ed6fc9fce25c6` / `6206b06fa93958911f4a9231b6152f7ff1470eb4` | The scoped #8574 result is retained by merged successor [#9217](https://github.com/Unjuno/agent-interface/pull/9217). The audit harness read a golden fixture from an uncommitted absolute path, so its test was not clean-checkout reproducible. | Preserve the scoped result and harness defect separately. Any harness repair is a new current-main change; do not repeat the consumed allocation. |
| [#8836](https://github.com/Unjuno/agent-interface/pull/8836) | Open, non-Draft; `afab8e406164e2e69de6ec25ba1724fa22f01d4e` / `f185a9059d485a4f8d5a65e9e7f6782897f67eae` | The completed audit retains `FAIL_COST_GATE_SCOPED`; this is a negative scoped result, not a passing cost claim. | Re-read its exact diff, evidence, dependencies, and current-main overlap before any state change. Repair accounting in a current-main successor; do not rerun the consumed allocation. |
| [#8840](https://github.com/Unjuno/agent-interface/pull/8840) | Closed; `7d9aba384b0d799119f330c9c763e60703ecc320` / `f185a9059d485a4f8d5a65e9e7f6782897f67eae` | A03 remains `HOLD_UNCERTAIN`: the candidate completed, but the auditor stopped on a reason-string mismatch. Its 2,231-file first-outcome archive and 17-member blob manifest were checked; merged successor [#9236](https://github.com/Unjuno/agent-interface/pull/9236) repairs the generated analysis index without rerunning candidate or auditor. | Keep the hold and the corrected index separate from a method conclusion. See [relative-view rotation features](../ideas/relative-view-rotation-features.md). |
| [#8841](https://github.com/Unjuno/agent-interface/pull/8841) | Open, Draft; `04e7ddaa583fb3b120e9f3d00f3249c79c304f04` / `f185a9059d485a4f8d5a65e9e7f6782897f67eae` | Construction-boundary tests are retained; the #59 live threat exposure is not established by them. | Preserve as construction-only evidence. Compare exact source/tests with current main and record transfer or a specific hold before considering PR closure. No live-control completion is claimed. |
| [#8843](https://github.com/Unjuno/agent-interface/pull/8843) | Closed; `4a9baf2d5e362de64c73c51cbfa18a2667c5f352` / `f185a9059d485a4f8d5a65e9e7f6782897f67eae` | Its authored-HUD cancellation construction and package are retained by merged successor [#9218](https://github.com/Unjuno/agent-interface/pull/9218), which repairs the seven manifest entries against the exact Git blobs. | Keep the original first outcome immutable; do not rerun the consumed candidate or treat construction as a live result. See the [#59 evidence-family record](../ideas/map01-live-guard-evidence-family.md). |
| [#8844](https://github.com/Unjuno/agent-interface/pull/8844) | Open, Draft; `b9f4221cdbee93e4186f19ab659f51dca0bc5cea` / `f185a9059d485a4f8d5a65e9e7f6782897f67eae` | A04 remains `HOLD_UNCERTAIN`; its candidate/audit archive is unique retained evidence. The candidate completed 360 trials, while the auditor stopped at `feature_loss-30090-viewstate_oracle`, step 0. | Preserve the original packet and hold; verify exact raw custody and any current-main transfer before closure. Do not rerun candidate or auditor. See [relative-view rotation features](../ideas/relative-view-rotation-features.md). |
| [#8845](https://github.com/Unjuno/agent-interface/pull/8845) | Open, Draft; `a8abd5afaccd35927752d857edfab679f96145c9` / `f185a9059d485a4f8d5a65e9e7f6782897f67eae` | The proposed verification depends on a shared WSLc lane whose owner/release is unresolved. | Keep on hold until ownership and release are explicitly verified. No WSLc/Docker operation or resource grant follows from this audit. |
| [#8848](https://github.com/Unjuno/agent-interface/pull/8848) | Closed; `6f95e7dc6d37e1dd97f5d47882796d94902478c7` / `f185a9059d485a4f8d5a65e9e7f6782897f67eae` | The A12 soft-ammo feedback packet and immutable raw are carried by merged successor [#9234](https://github.com/Unjuno/agent-interface/pull/9234); seven CRLF-derived checksum entries were corrected against exact Git blobs without rerunning the consumed WSLc test. | Use the successor packet and preserve the original outcome. This does not establish the broader #59 live-control or safety hypothesis. |

## Boundary and next finite work

Four PRs in this cohort are closed with the scoped successor trails above.
Five remain open, but none is a blanket merge/closure candidate: #8702 has a
raw-custody gap, #8836 has a scoped cost failure and stale base, #8841 is
construction-only, #8844 retains a unique uncertain first outcome, and #8845
is blocked by shared-resource ownership. Recheck live state before any future
mutation. The next software-only action is to compare #8836 and #8841 against
current main and write separate transfer/hold decisions; keep #8702/#8844
evidence intact and leave #8845 untouched until its owner releases the lane.

No issue was closed, no experiment was rerun, and no branch or worktree was
removed by this audit integration.
