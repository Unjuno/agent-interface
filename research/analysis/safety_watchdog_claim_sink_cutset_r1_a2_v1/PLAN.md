# #1906 — typed claim-sink cut-set transfer A2

Task `SAFETY-WATCHDOG-CLAIM-SINK-CUTSET-R1-A2-20260919-001`.

Successor to #1893 `STOP_FORMAL_HARNESS_MUTATION_INVALID`. No #1893 scientific result is pooled.

## H/T/D/C/U

H: unchanged from #1893. Exact retained #827 source must be typed by claim sink: release verification is upstream of journal/ordinary-pipe work; local durable receipt survives the ordinary-pipe fault domain but not its own journal fault; republished receipt is reached only after the parent recovery/drain phase; pipe-only has no local durable/recovered evidence path under the retained blocked-pipe exposure.

T: same three byte-pinned #827 source files, same five typed graphs, same #1882 reachability theorem and same independent audit. The only A1→A2 repair moves the complete two-line candidate `if` block in the corruption control, rather than removing its sole body statement. The mutated control remains syntactically valid and must still be rejected by the source-order validator. One formal invocation after remote source freeze; no X11 rerun.

D: `PASS_WATCHDOG_TYPED_SINK_CUTSET_SCOPED` only if source hashes, source-order facts, all five graph classifications, theorem/direct reachability equality, four corruption controls and independent audit all pass.

C: static Python source order does not model hidden library/kernel/X-server/filesystem dependencies.

U: external dependency-edge completeness remains unknown; no statistical or hard-real-time claim.
