# Post-run duplicate allocation consumption

The launch-time failure recorded in `REPORT.md` progressed into two completed executions of the same named frozen allocation.

## Observed completion

GitHub Actions runs `34968759795` and `34968781910` both completed the step named `Run frozen one-shot MAP01 measurement allocation` successfully and each uploaded an artifact named `map01-measurement-integration-live-02`.

The artifacts are distinct:

- run `34968759795`: artifact `10396069016`, 943,528 bytes, `sha256:dabbc5630b99bde994c3595d09e3a414a3571960b755bc26cedcfd638829f375`
- run `34968781910`: artifact `10396068909`, 943,306 bytes, `sha256:274623504341e6e3419c07b1f07368ca4e0e87078d72ebe507ce925ee670813f`

Both retained audits report `PASS measurement integration`, one completed hold, two release transitions, 19 scorer samples and zero positive useful events. Their intent tokens and measured held-input bounds differ, so these are separate executions rather than byte-identical duplicate artifacts.

Descriptively, the retained lower bound for key `a` differs by 5.645 ms and key `d` by 5.638 ms between the two runs; the release-batch median differs by 30.226 microseconds. These differences are **not** treated as a comparison or distribution because the allocation was specified as one-shot and was accidentally/ambiguously consumed twice.

## Disposition

**RETAIN BOTH RAW OUTCOMES; DO NOT POOL THEM.**

The mechanics success of both executions does not repair the orchestration failure. A later coordinator should explicitly choose which run, if either, is the canonical first-outcome record for the consumed allocation and must preserve the other as duplicate-allocation evidence rather than silently averaging or deleting it.

No rerun is justified by this finding. The next launcher revision should prevent multiple active run IDs for one explicit allocation identity before the formal step begins.
