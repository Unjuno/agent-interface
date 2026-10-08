# T2 report — Issue #6147

**Result: `H_PASS_SCOPED` for the frozen deterministic disposable Xvfb fixture only.** The three arms each produced ten rows and completed with candidate and fixture exit 0. The separate raw-only auditor returned `PASS_RAW_REPLAY` with zero errors and rejected all five frozen corruption controls.

Adaptive produced six verified effects: two for the action-different separable A/B pair, two for action-equivalent C/D, and two after I/J converged to shared current terminal Z. It used 16 safe probes and zero unsafe probes. No-probe and one-step each produced only the two C/D COMMON effects; both yielded on separable A/B, impossible E/F, stale/expired G/H, and convergent I/J. No arm selected U. These outcomes satisfy the declared bounded fixture hypothesis; they do not establish a real-application benefit or safety guarantee.

The T1 predecessor remains `STOP / NOT_EVALUATED`, with one adaptive candidate exit 1 at Xlib cleanup and no auditor or remaining arms. T2 introduced only a narrowly scoped close-time exception, reproduced the same teardown ordering in a construction-only run, then completed its own independently preregistered allocation once. T1 raw and report were not modified to turn that STOP into a pass.

Formal outputs, container inspect records, fixture oracles, exits, and auditor output are retained in `raw/formal_02/` and bound by [the raw SHA-256 manifest](raw/formal_02/SHA256SUMS.txt). Allocation details and environment are in [RUN_RECORD.json](RUN_RECORD.json); frozen H/T/D/C/U and limits are in [PROTOCOL.md](PROTOCOL.md) and [FREEZE.json](FREEZE.json).

## Local verification

The updated repository analysis workflow was exercised locally: 109 tests across all 18 configured suites passed. Its geometry-feasibility provenance suite was run against the exact frozen historical workflow source required by that test; the current workflow was restored byte-identically and its SHA-256 rechecked. At allocation base `511ff52`, the generated analysis index passed at 554 retained entries and public navigation passed at 26 documents / 1,565 links. After rebasing onto `c2dc6e4`, the analysis index passed at 557 entries and public navigation at 26 documents / 1,571 links. The branch was then rebased onto latest main `87959b5`; the analysis index passes at 558 entries, workspace index reaches 156 directories, and public navigation passes at 26 documents / 1,577 links. The index unit tests pass 17/17, workspace-index tests pass 21/21. T1 and T2 package suites pass 13/13 and 16/16, respectively; T2 also passes 16/16 in the pinned container. #6505's integrated test suite passes 7/7. Additional latest-main suites pass for #6243, #6225, #5890, and #5368; two executable integration assertion scripts pass from their package directories. A blanket recursive unittest discovery was not a supported runner for those files and was not counted as CI.

The preregistered manifest digest is preserved; the post-run README status update changed its documentation hash entry. All executable sources and frozen inputs still verify, and the full formal raw has a separate verified manifest. This is documented explicitly in [POST_RUN_PROVENANCE.md](POST_RUN_PROVENANCE.md).

## Limits

This is a single authored deterministic fixture with a finite known state support, stationary pixel rendering, supplied public family labels, and harness reset. Effects are in-memory receipts. There is no real application, user workflow/data, model, GPU, network, external effect, latency, task-utility, or production-authority evidence. Ordinary typed queries or YIELD may be preferable. A pass here is not proof of general GUI observability, safe probing, or usefulness. Keep Issue #6147 open for actual transfer evidence.
