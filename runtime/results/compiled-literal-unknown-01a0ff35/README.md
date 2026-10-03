# Declared literal unknown at the compiled effect gate

Refs #6932 / #57. Ordinary private engineering repair on base816724f93a7239b3ad9b5ebb2e5f79b8a103b2db.

The validated language allows scalar strings. A pending effect explicitly expecting the string `"unknown"` previously stopped before its required effect verifier even when the fresh observed string matched. The candidate lets that exact declared literal reach the same verifier. It does not turn a predicate match into an effect certificate.

## H / T / D / C / U

- H: an explicitly matching scalar literal reaches effect verification; missing values, legacy nonmatching unknown, exact-type mismatch and unavailable/failed verdicts retain stopping/prefix semantics.
- T: actual graph with a private inert Driver, actual guarded adapter with a private inert Bridge; first7 core controls and2 composition controls before repair; targeted9 and complete core83 methods normally and optimized. The separately pinned success-reference dependency adds4 focused controls for13 combined methods normally/optimized.
- D: retain all first failures and source/command hashes; require matching literal continuation only after verifier success, no second action on negative verdict, and unchanged prior typed/freshness/release/budget controls.
- C: the string can be a legacy unavailable marker or an explicitly authored desired value. The expected contract disambiguates the literal case; callback truth is not inferred from spelling. This is not an application-semantic verifier.
- U: caller callbacks remain trusted. With an expected literal unknown, unavailable observation must be an absent predicate or an unavailable verifier verdict. No general GUI/task/release/timing/model claim, sandbox or raw authentication.

## Actual results and inputs

First core7 retains4 failing assertions, exit1; separate guarded2 retains3 failing assertions, exit1. Candidate targeted9/9 and core83/83 pass normal/-O. Pinned private composition with#6900 head4a3c51dd86c592892fa92df523b822e7bce548e2 passes13/13 normal/-O. Source, stderr and stdout are retained with UTC/argv/exit/hash receipts. `REPORT.json` gives each actual method count and source scope; no full native/hosted CI was run.

`SOURCE_FREEZE.json` pins14 exact base inputs before the first regression; `GUARDED_SOURCE.json` pins7 more unchanged adapter/test inputs before its first regression. `NATIVE_SELECTION_*` pins the shared runner and proves exactly one added module in each existing suite, without changing other suite entries/order. The runner is production configuration; its current command now selects the new controls, while workflow bytes/triggers remain unchanged.

`DEPENDENCY_COMPOSITION.json` records a private source-bound combination, not adoption or approval of#6900. Application requires that separately owned success-reference guard's actual valid delivery and a fresh nonauthor current-source/tree comparison. A changed dependency/head/validation contract needs renewed content review. Existing callback-custody and capture-order delivery units remain independent; later materially changed compiled dependencies must be reviewed.

## Preservation and reproduction

All source snapshots under source/ are inert `.py.txt` evidence. Original unredacted files and command records remain private. `PUBLICATION.json` binds each username-only derivative to its original hash/length; stderr CRLF and all nonusername bytes are preserved. `EXECUTION_CONTEXT.json` explicitly distinguishes source-derived cwd context from the original receipt fields. No original receipt or first failure was rewritten. Receipt stream hashes refer to original unredacted streams; for a derivative, its PUBLICATION original hash must join that field and its published hash must join the actual file/MANIFEST. Do not claim original-byte identity for a redacted log.

On the same checked source/dependency environment, focused ordinary regressions are:

    python -B -m unittest -v runtime.core_v1.test_compiled_literal_unknown_01a0ff35 runtime.guarded_x11_v1.test_compiled_literal_unknown_01a0ff35
    python -O -B -m unittest -v runtime.core_v1.test_compiled_literal_unknown_01a0ff35 runtime.guarded_x11_v1.test_compiled_literal_unknown_01a0ff35
    python -B -m unittest discover -s runtime/core_v1 -p 'test_*.py' -v

The committed source manifest qualifies the checked copies and historical baseline; it is not a statement that future main has those bytes. Dynamic proposals/votes/apply records stay outside this tree. The new test modules contain no backend/input/display/model execution. Existing guarded tests use private in-memory images and an inert Bridge; NativeHandleBridge is not instantiated.
