# Terminal-epoch-01 independent saved-data review (T1, 2026-10-04)

## H / T / D / C / U

**H:** The committed terminal-epoch-01 package is complete against its own file manifest and binds its retained V15/ProgressClock source copies to the declared frozen source commit. An independent parse of the 57-row result should confirm advancing producer tics, equal before/after tics per acknowledged update, coherent frame tics where available, one negative no-exit terminal event, and successful engine close.

**T:** Verify every path and digest in the source package's `FILES.sha256`; confirm the two committed source files match both their frozen-commit blobs and retained copies; inspect the probe's no-button/no-input call surface; and independently check chronology, event cardinality/polarity, exit receipt, and close fields in saved output. No container or game process is launched.

**D:** `PASS_TRACE_AND_SOURCE_BINDING_WITH_SCOPE_LIMITATIONS` only if all package hashes and source bindings match, all 57 rows satisfy the stated trace invariants, and the raw result agrees with stdout/exit receipts. Any mismatch fails the audit.

**C:** The saved package, probe, and reported output share one experiment path and may share a common implementation or serialization fault. This review independently checks internal consistency and exact committed source identity, not the historical host execution itself.

**U:** The WAD bytes and execution environment are not retained here; only the WAD digest, requested resource settings, stdout/stderr, and exit receipt are available. The raw repeated-terminal outcome omits the repeated sample timestamp. The record cannot establish actual timeout onset independently, runtime memory enforcement, neutral cadence, physical input release, task effect, or gameplay efficacy.

## Result

The audit verifies the file manifest, frozen source ancestry, and the 57-row trace. Producer tics advance from 5 to 71; each explicit update is bracketed by the same producer tic; 56 frame tics match their producer tics; and the final sample yields exactly one `EPISODE_FINISHED_NO_EXIT` event marked negative, unuseful, and controller-invisible. The retained result reports zero positive input calls, successful close, and a stopped engine. The stderr cgroup/swap warning is retained and prevents treating the requested memory limit as proven.

This does not rerun or replace the already completed construction experiment. It is an additive saved-data audit of the exact package on current `main`; the broader live threat-control gate remains open.

## Reproduction

From the repository root, run `python research/doom/terminal_epoch_59_4d74_20261004_independent_review_t1_20261004/audit.py`. It reads only the committed package and Git objects and writes `audit-result.json`.
