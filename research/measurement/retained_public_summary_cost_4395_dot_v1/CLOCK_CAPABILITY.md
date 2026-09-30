# Clock capability decision before any candidate call

The reviewer initially held measurement because a different retained visual harness had many zero process-CPU deltas and positive deltas around4ms. Read-only source comparison verified that visual run.py SHA256125493f079d5090e1cc569c9aa8217a0a181bb904ddabbe983e5a00cacdedf8e matches its frozen identity and uses direct time.process_time_ns around encoding. The present harness uses the same API; no unit conversion or rounding explains the difference.

The parent authorized one separate generic clock-capability construction, with no candidate import or corpus read. It ran32 fixed arithmetic blocks,10000 iterations each, one CPU,256MiB address-space limit,1s CPU and outer wall limits. Observed total block wall time was47,678,572ns. Exit0, empty stderr. All32 process and32 thread CPU deltas were nonzero, about1.38–1.87ms, with non-4ms-quantized values.

These current observations do not explain the older discrepancy, show a universal environment change, or prove sufficient precision for cheaper three-call projection batches. They only justify not assuming a universal4ms CPU floor. All capability source/raw/command/exit bytes are retained here; RESULT.json SHA256c8f6f36788641af538bf8810424868021e2227e3553b752a026954f316447ab1.

The reviewer accepted retaining the unchanged225-call protocol, conditional on freezing this provenance. The actual scientific invocation must still satisfy every aggregate-resolution guard or STOP without expansion, retry or tuning. The scientific runner, oracle, source modules, inputs and schedule are unchanged from pre-review/FREEZE-02.json (SHA25653126d8792f7d4d6e0d853f368d2b6dd69325298bd6503dc7f96ba3b16fe5b23). Formal invocation count remains0. Capability construction is separate and is not a projection performance result.

