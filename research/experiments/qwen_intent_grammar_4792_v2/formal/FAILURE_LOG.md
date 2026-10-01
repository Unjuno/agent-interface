# Formal outcome — Issue #4861

Allocation `qwen-intent-grammar-4792-recovered-20260927-02`, seed 4792962, ran once on local Docker image `sha256:63ce8205b5e0cf7daddac087d6c1bd5489d51e3af345cf923af925026bdd600c` (linux/amd64), CPU-only, float32, 2 intra-op / 1 inter-op threads, eager attention. Docker Engine client/server 29.8.0. Formal container limits were 2 CPUs and 8 GiB RAM, with network disabled, root/source/model/adapter/input read-only, and no GPU request. One model load completed; 64 greedy generations completed for 32 paired rows; no fit or optimizer update occurred. Exit code 0; `RAW.jsonl` is 357,916 bytes, SHA-256 `c450980bf1f4fd6ba389e7eeaf38e07739e6c7def00dbd2e719af0eb27f8a344`.

Transformers emitted: “Sliding Window Attention is enabled but not implemented for `eager`; unexpected results may be encountered.” This warning is retained as a model/runtime limitation; the frozen run was not changed.

The independent raw-only audit completed 894 checks with `integrity_pass=true`, no audit errors, and zero unsafe bound effects. The preregistered semantic gate failed: free exact intent 13/32 (40.625%); constrained exact intent 4/32 (12.5%); paired delta −28.125 percentage points. Constrained outputs were canonical JSON and in the visible-state candidate set 32/32, but that syntax/candidate validity did not translate to correct intent. Free candidate membership was 7/32. Exact class counts are in `AUDIT.json`.

The separately run corruption-control harness returned 7/8 rejected and failed its gate. Its `alter_constrained_text` case assigned `{"op":"save"}` to row 0, whose original constrained output was already exactly `{"op":"save"}`; this was a no-op and therefore did not test auditor rejection of changed evidence. The raw artifact and harness source are preserved unchanged. No control mutation, retry, tuning, or second audit/control invocation was made.

Disposition: retain **FAIL_DIAGNOSTIC_GATE_AND_CORRUPTION_CONTROL_GATE**. Do not report this as a successful diagnostic, retry the allocation, close #4861 as completed, or merge it as a verified pass. Full input, raw output, and local invocation context remain on the PC under `formal/input/`, `formal/output/formal-01/`, `formal/audit-01/`, and `formal/controls-01/`; sizes and SHA-256 values are in `RESULT.json`. The GitHub handoff contains the compact result/audit/control receipts, not the per-row raw output or base model.

For the complete frozen commands, see `PREREGISTRATION.md`. No GitHub Actions or other external workflow was used.
