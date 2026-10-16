# Rescue qualification — Issue #5156 T3 (2026-10-03)

This is a custody-only transfer from Draft PR #5630, exact source head
`be1483ed1765f173840894dc51f2b9533b1e9fc3`. The 106 files in the original
T3 package are retained byte-for-byte. The current `research/live_control`
navigation README receives one additive qualification entry; the old source
branch does not replace current-main documentation.

## H / T / D / C / U

- **H:** The package's host-only construction says that storing complete
  32-byte XQueryKeymap snapshots and auditing every expected case/stage can
  independently check X-server key state more strongly than runner booleans.
  This is not physical key occupancy or proof that an application consumed an
  input event.
- **T:** At the exact source head, reran its README-prescribed synthetic/unit
  suite from an isolated archive using CPython 3.12.13: 35/35 passed. Verified
  all 11 retained per-run SHA256SUMS manifests. The source package's own
  whitespace diff is clean. The first rescue-PR analysis-index run failed
  before test execution because its sparse checkout omitted this package's
  working directory; the checkout is now extended by the exact package path
  and requires a clean rerun.
- **D:** The immutable `construction-cli-11` record is a synthetic candidate
  plus separate raw-only auditor construction. It records 25 synthetic raw
  rows / 9 keymap snapshots and `PASS_SYNTHETIC_RAW_ONLY_CLI_BOUNDARY`; this is
  not a formal candidate/auditor result. The original PR's `method-t0` check
  failed at its repository-wide `git diff --check` step, which reported
  whitespace in paths outside this T3 package (including `research/system1/`
  and `runtime/host_v1/`); the T3 package-scoped whitespace check is clean.
  The original `audit`, `container-construction`, both `method-audit`,
  `native-construction`, both `native-mcp`, and `replay-gate` checks passed.
  The method-t0 failure is retained and is not represented as a package test
  failure.
- **C:** No formal X11/Docker candidate, trusted host-launch receipt,
  GUI/application effect, physical key-up, or MAP01 interaction was produced.
  The source record reports no exclusive allocation or trusted receipt signer.
  The passing CI `container-construction` check is construction validation,
  not the missing target formal experiment. Formal candidate/auditor counts
  remain 0/0; the 35 tests and synthetic CLI are construction evidence only.
- **U:** A known completion-sentinel defect remains unresolved. In
  `audit_formal_x11.py`, completion rows are first filtered with
  `row.get("exit_code") == 0` and only then counted. Python equality admits
  `False` and `0.0` as zero and can hide additional nonzero completion rows;
  the source PR's independent review also identifies success-plus-failure
  cardinality and Boolean/float counterexamples. This archive does not fix or
  waive that defect. Any formal successor must close those controls, obtain a
  fresh exclusive allocation and trusted host receipt, and preserve all
  predecessor outputs.

Issue #5156 remains open, and the earlier results, STOPs, and review findings
are unchanged. No safety, latency, physical-key, application-effect, or
efficacy claim is made.
