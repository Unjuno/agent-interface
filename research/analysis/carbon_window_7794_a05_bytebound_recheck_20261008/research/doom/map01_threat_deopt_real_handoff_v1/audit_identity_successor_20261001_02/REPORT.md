# Issue #626 T1 — exact-source audit differential

## Result

**`PASS_AUDITOR_SEMANTIC_COMPATIBILITY_AND_IDENTITY_SCOPED`** for this finite synthetic contract only. The exact frozen legacy auditor source was extracted read-only from the hash-matched `source_bundle.tar.xz`; its SHA-256 is `7ab3d8895c9e8d7c80cf4ff463bac0623fb39247f8aa0d65d34941a1f8c48a40`. The harness ran once, with no candidate invocation and zero formal/live rows.

Both the exact legacy auditor and T0's independent successor passed the pristine six-row synthetic fixture. Both rejected all 12 semantic corruption controls: threat release, active deopt, missing score/signal, traceback, baseline stale-selection/release, candidate stale selection/admission/fresh selection/release, and incomplete schedule. The successor rejected all five row-identity mutations (`id`, `pair`, runtime bundle SHA, fixture ID, fixture seed); the exact frozen auditor accepted all five with no errors. This supports the successor's tested semantic compatibility while confirming the specific identity-binding gap on exact source.

## H / T / D / C / U

**H.** The successor preserves the legacy auditor's semantic rejection behavior on the 12 frozen controls while binding row identity fields omitted by the legacy audit.

**T.** Reuse T0 synthetic raw bytes SHA-256 `121b04c7da14f9e0e0bd1a6a960a2ffbfd22ef879b1d547862191639c5e7a4ce` and fixture SHA-256 `136439478eaa4950668ff28cbe945558229619b5c9a8392de9b27b2ffe04dae8`. One Python differential harness invocation compared the exact archived auditor and successor across a pristine baseline and the frozen mutation matrix. Exact source/member hashes and the harness inputs were rechecked after execution. No container, ViZDoom, X11, model/provider, GUI, or input.

**D.** Both pristine passes, 12/12 semantic rejections by both, and 5/5 identity rejections by successor plus 5/5 acceptances by legacy were observed; all frozen hashes matched. Result: scoped PASS.

**C.** Hand-authored mutations and six deterministic synthetic rows. This is finite contract testing, not fuzzing or game evidence.

**U.** Does not validate live #626 rows, runner authenticity, real MAP01 handoff efficacy, or the container gate. It does not alter the prior T0 STOP artifact: T0's local transcribed comparator hash mismatch remains preserved as a provenance error. T1 separately recovered and used the exact original source; the previously published Issue probe independently records the same identity gap. Formal schedule remains 0/6 and #626 stays open. Independent code review is still needed before using the successor for any formal allocation.

## Reproduction

From this directory, with Python 3: `python3 -B -m unittest -v test_differential.py` (one pre-freeze construction test) and `python3 -B differential.py` (the one frozen harness invocation). Source: `legacy_audit_exact.py` is unchanged from #626's six-member archive; `audit_v2.py` is unchanged from T0. Raw output: `differential_result.json`; identities: `FREEZE.json`, `SHA256SUMS`.
