# Scoped local verification

All commands below ran on the recorded Windows / CPython 3.11.9 host.
Exact UTC process starts/ends, argv, exit status and original/published output
hashes are in logs/. No original matrix or audit attempt failed or was replaced.

| Check | Result | Scope |
| --- | --- | --- |
| Frozen four-arm direct admission matrix | exit 0; 36,000 rows | One invocation; no backend import/invocation |
| Independent raw reconstruction | exit 0; 9,000 combined matches | Strict JSON type identity, exact fixtures and coverage |
| Negative controls | exit 0; 6 raw + 4 source mutations detected | Original raw/source files unchanged |
| Complete relevant core suite in exact-byte private export | exit 0; 78 tests | Baseline core plus both PRs' exact regression modules |
| Core doctor in that export | exit 0 | native_backend_loaded=false; input_authority=none |
| Workspace committed-tree index | exit 0; 156 directories reachable | Existing script, exact current source-freeze Git tree |

The private core export's 13 actual Python files match CORE_SUITE_MANIFEST:
unchanged files come from the pinned main, the two added test modules from their
exact PR heads, and contract.py from the conflict-free three-way source merge.
No broader native/CLI/distribution, host-foreign-platform, model, container,
live-input or hosted CI run is claimed. Optimized Python was not additionally
rerun. This package does not change shared code, workflow, top-level namespace
or a common index. Evidence scripts are explicitly invoked; their copied
regression directory has no package initializer and is outside the core test
discovery path. No test-discovery/default/runtime promotion is requested.

An early intake read used nonexistent test_core.py (the current source is named
test_contract.py), and a no-checkout clone required populating its sparse index
before reading files. Those read/setup errors occurred before freeze; no matrix,
backend or formal allocation ran during them. Exact-Git source export, freeze
and all construction outputs described above followed that repair.

Final publication checks additionally verify frozen source pins, all package
SHA256SUMS against staged Git bytes, syntax, Markdown file/directory targets and
base-to-head diff whitespace. Dynamic final head/commit check records are kept
outside the approved source tree to avoid self-referential hashes. Hosted
checks, required protections, nonauthor content approvals and final application
are separate and not represented as passed here.

The first publication whitespace check flagged CR bytes in original Windows
command logs as trailing whitespace. A separately retained pre-repair diagnostic
readback exits 2 (logs/publication-whitespace-readback.*). The original logs,
raw, freeze and candidate/auditor source bytes were preserved. A local logs-only
attribute recognizes CR at line ends while retaining the other whitespace
checks; this is a publication-format correction, not an experiment rerun.
