# Issue #7418 T0 — formal result

**Status: `PASS_METHOD_SCOPED`.** This is a finite proposal-representation
result only; it is not evidence about learned memory, deployed agents, real GUI
work, or action safety.

The preregistered candidate and independent auditor each ran once under host
CPython 3.12.13, with no retries. The candidate emitted 51 rows across three
representations and 17 frozen queries. The raw-only independent audit
reconstructed all 51 rows and returned `PASS_METHOD_SCOPED` with no errors.

| Representation | ACCEPT | REJECT | UNKNOWN | Key result |
|---|---:|---:|---:|---|
| Exact episode retrieval | 9 | 1 | 7 | Exact evidence is conservative on held-out contexts. |
| Unqualified majority | 17 | 0 | 0 | Accepts protected forbidden, contradictory, and unrepresented cases. |
| Exception-preserving | 13 | 2 | 2 | Rejects both protected queries; abstains on both ambiguity controls. |

The exception-preserving representation accepted all 12 common-safe queries
(100%; frozen minimum 90%) plus the high-contrast specificity control. It
rejected both protected queries (zero false acceptance), classified the
contradictory and unrepresented queries UNKNOWN, retained all 12 source IDs,
and passed the source/provenance checks. Each representation satisfied the
12-record and 8192-byte limits. The auditor rejected all four preregistered
corruptions: dropped exception, inverted exception decision, removed mode
condition, and derived-as-observed provenance.

The finding supports only this finite fixture and stipulated predicate/effect
oracle: preserving a source-linked applicability exception can prevent the
specific majority-generalization error while retaining the tested common
coverage. Exact retrieval also avoids that false acceptance, with lower
coverage. No model generated the rules; all rows and rules are deterministic.

## Reproduction and custody

Frozen source and preregistration: commit `bbab20f25015021cb3ec9ce7c7306d2679f5e208`;
GitHub Issue #7418 preregistration comment ID `5978067727`. Exact commands and
source hashes are in `FREEZE.json`. Formal invocation counts are candidate
1/1, auditor 1/1, retries 0. Raw output and audit are under `formal_01/`;
their hashes are in `SHA256SUMS`. Construction and post-run contract tests are
not additional formal CLI invocations.

Container use was not required by the Issue's explicit finite no-model/no-GUI
scope. No action execution, user data, network, GUI, GPU, or model was used.
