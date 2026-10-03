# Retained browser audit correction v2

Parent PR6920 / Issue6501, ordinary evidence-integrity repair by existing worker `01a0ff2d-be6f-78d3-ad7c-497514c9079f` under FINAL-v5. Originating review5398947004, inline4171650135/138/140 and coverage supplement5965577562 identify three finite raw-contract omissions. The original 72-file package, auditor, A01 client/server, first streams, source freeze and experimental decisions stay unchanged. The input copies here are byte-identical retained originals, not additional cohorts or browser runs.

## What changed

`audit_v2.py` is a separately versioned raw-only copy of the original oracle. It now checks each offered cohort contains its actual waiter starts/decisions/ends and relevant local event times; leading warmup events remain a separately accounted pre-offer prefix. It requires an exact integer final generation. It joins exactly one start, delivery and decision per waiter, with strict read IDs, exact scopes/deadline/decision-clock mirrors and local event ordering within that waiter. Server and client clock domains are not compared numerically. Any audit errors suppress the derived latency-benefit flag to unavailable (`None`), rather than treating invalid timing as a measured gain. No producer, broker, gate, UI, workload, comparison threshold or runtime source changed.

The actual start timestamp is recorded before the `waiter_start` journal entry. The correct constraint is `started <= waiter_start event <= delivered event <= decision <= decision event <= ended`; equality between actual start and its later journal timestamp would reject valid originals. The decision's explicit `ns_decision` must exactly match the consumer mirror. This is finite record consistency, not protection against a coordinated fabricated emitter or proof of physical effects.

## Before and after

The ordinary first regression invocation used byte-identical v1 as the candidate: 4 test methods, exit1, 82 subtest failures. It accepted all72 reviewer-family copies plus10 of12 supplementary copies; two supplementary missing/duplicate-event cases were already refused by v1. Original15 conditions/30 waiters and the existing12 controls passed. This is an expected regression RED against the incomplete auditor, not a rerun of browser A01.

The versioned repair was checked one family at a time:15 zero-duration cohorts,27 same-value final-generation aliases (15 floats/12 Booleans),30 nonexistent delivered reads. All copies start from parsed original data, never accumulated mutations. Twelve additional finite custody/interval controls cover numeric delivery aliases, scopes, decision read/time, start deadline/scope/request, absent/duplicate delivery and truncated/offered-late cohorts. Final4 test methods pass, all72+12 copied controls reject and existing12 controls remain effective. The original elapsed values, offered reads10/6/8, warmup reads1/1/1, correct effects9/7/9 and refusals1/3/1 reconcile unchanged.

The first attempted delivery join repair shadowed the condition variable `kind` with a new event-loop variable, causing60 original-data errors. That candidate source and failed test exit1 are preserved under `evidence/after`; only the new loop variable was renamed to `event_kind`. The unchanged tests then passed under `evidence/after-fix`. An earlier family-only assertion failure is preserved as a tool-output projection with no invented native clock/PID. Cohort intermediate source bytes were reconstructed by reversing the single next typed-generation edit and checked against the already recorded SHA256; this is labeled reconstruction, not a claimed original source snapshot.

Final auditor SHA256 `400b782260daf3b0fe4ebd5d06b79057cf00d7dde277acc2eda1f64ee2f5df36`; unchanged regression-source SHA256 `5b88d97428920c7fc2b5a7ee7fcd0f2ae82582ca2ca7ce09728461ca0af22693`. The author's72 JSON path/value recipes SHA256 `2bbbc6715df29c1ac072a07cd4a4d5198c369c3443bdab9937f3284135ec2954` use UTF8 sorted-key compact JSON, ensure_ascii=true, no newline. This is the author's explicit specification; the independent reviewer's differently serialized specification SHA26333d... is not asserted identical.

## Recheck

From this directory with stdlib Python3.12:

```sh
python -B regressions.py
python -B compare_retained.py NEW_COMPARISON_OUTPUT.json
python -B audit_v2.py inputs NEW_REAUDIT_OUTPUT.json
```

Every output is exclusive. The original `audit.py` remains available unchanged in the parent package and as exact `inputs/audit_v1.py`. `regressions.py` imports only auditors and retained JSON. No candidate/fixture/browser, native input/display, model, GPU, container/shared runtime or original formal allocation is invoked. The actual ordinary environment was native Windows / CPython3.12.10, no external Python dependencies.

First native regression command/PID/start/end/streams/hash records and tested source versions are retained. Family/comparison/CLI commands which completed directly through the tool are explicitly described as tool-result projections where native stream receipts were not captured; no missing timestamps are supplied. Public path/text/JSON-format projections are listed separately, and private-original stream hashes in receipts continue to refer to retained private bytes. Public manifest hashes the projected public bytes.

## Interpretation and adoption

Unmodified A01 still meets only the authored fixture decision rule. The deliberately serialized180ms read service, one cohort per condition, unknown host background load, failed pre-execution HTTP503 remote publication, same-author oracle and previously stated scope remain. This correction provides no new actual task, latency, tokens, resource, native release or live-display observation. It does not upgrade fixture RETAIN to production/composition adoption; that remains HOLD. The former v1 nonauthor review and original failure remain in place. A fresh head/proposal/committee epoch must be reviewed before any new counted approval; current-main combination, applicable rules and one conditional history-preserving application remain separate.
