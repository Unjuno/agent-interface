# #5598 T0 — retained paired synthetic route outcomes (read-only)

## H/T/D/C/U

- **H:** Matched route-A/route-B outcomes can expose a conditional-rescue difference from route B's marginal success in a declared shared-failure stratum.
- **T:** Read the existing #5424 `raw/formal/inputs.jsonl` through GitHub MCP. Pair the two potential primary outcomes already present on each exact `(regime, rep, t)` row; summarize `P(B=ok)` and `P(B=ok | A!=ok)`, plus B severe/catastrophic outcomes. No policy outcomes are used to invent counterfactuals, and no source or raw is changed.
- **D:** Data-availability gate passes only for this synthetic event corpus if all 18,432 rows contain both route outcomes and a shared incident marker where declared. This is not #5598's GUI/task-family hypothesis gate.
- **C:** Route values are authored simulator outcomes, not independently implemented GUI controllers; repeated time rows within a replicate are dependent. `A!=ok` includes `transient`, which is not necessarily refusal or failure of an application task.
- **U:** No GUI, task obligation, live actuation, independent effect oracle, unsafe-replay, causal, confidence-interval, or production claim follows.

## Provenance and method

Repository: `Unjuno/agent-interface`, main at intake `9fc98feb617c26fe1baa7ecc4decd43b69df8601`. Source report: `research/analysis/action_class_error_budget_5424_t2_v1/REPORT.md`; source execution and manifest: `EXECUTION.md`, `SOURCE_MANIFEST.md`. The input blob was read as Git blob `69abacc463ec432c9863a6d38e8267413accd708`; outcome blob `517b4a76e86cb2fbdc9069e3eddb7f0155fbb48d`. Both blob identities were re-read at the stated main SHA. The full input text had 18,432 JSONL rows (3,737,839 UTF-8 characters); outcomes had 55,296 rows (20,392,581 characters). The retained source manifest declares the inputs SHA-256 as `cdc4ef16c30ec667c0cd043d1d69e2625b36fba4d14a3c50e27245c2e9330e8b`.

For each input row, `A non-OK := A != "ok"`; conditional rescue is `B == "ok"` among those rows; unsafe proxy is `B in {"severe", "catastrophic"}`. These are descriptive simulator labels only. No inferential test is appropriate for this post-hoc, autocorrelated fixed corpus.

## Results

| Synthetic regime | Rows | A non-OK | B marginal OK | B OK given A non-OK | B severe/catastrophic given A non-OK |
|---|---:|---:|---:|---:|---:|
| stationary | 4,608 | 364 | 4,245 / 4,608 (92.1%) | 342 / 364 (94.0%) | 3 / 364 (0.8%) |
| route drift | 4,608 | 985 | 4,249 / 4,608 (92.2%) | 912 / 985 (92.6%) | 11 / 985 (1.1%) |
| rare catastrophe | 4,608 | 617 | 4,274 / 4,608 (92.8%) | 568 / 617 (92.1%) | 3 / 617 (0.5%) |
| common cause | 4,608 | 740 | 3,798 / 4,608 (82.4%) | 405 / 740 (54.7%) | 282 / 740 (38.1%) |

Within common-cause rows carrying a non-null incident identity (720 rows), A was non-OK on 461; B was OK on 153/461 (33.2%) and severe/catastrophic on 278/461 (60.3%). This is a large conditional association in the synthetic common-cause fixture, not a GUI route result or causal estimate.

The matched-potential-outcome data-availability check therefore passes for #5424's synthetic event generator. It does **not** satisfy #5598's first useful empirical support gate for real tasks: no shared GUI task IDs, route implementations, refusals, independent effect receipts, or reset-matched application runs are present. Disposition for transfer to GUI: `STOP_DATA_SCOPE_MISMATCH`; no new GUI experiment is authorized or claimed by this read-only analysis.

## Reproduction and validation

The retained local candidate command was `python audit_joint_outcomes.py inputs.jsonl --out RESULT.json`. Exact input SHA-256 recomputed locally: `cdc4ef16c30ec667c0cd043d1d69e2625b36fba4d14a3c50e27245c2e9330e8b`, matching the source manifest. Output SHA-256: `1e8770ea31eeba110dd866412f774e2a18f3875b22846ff6f488382d302d69aa`. `audit_joint_outcomes.py` SHA-256 `b618f775749c50d63df9e4bd1bb021005dc7370371bbf79b3a0f77248a75e14`; `test_audit_joint_outcomes.py` SHA-256 `c13a6eb24d3d02fd3c45e33d474c2f466fad3fc399b79dcf05b84f4a222b564e`.

`python -m unittest -v test_audit_joint_outcomes.py` passed 6/6, and `python -m py_compile audit_joint_outcomes.py test_audit_joint_outcomes.py` exited 0. Tests cover paired conditioning, non-OK classification, severe-only conditioning, incident stratification, empty denominators, and exact-byte hashing. These are construction checks, not an independent raw-only audit of the original #5424 result.

No Docker/OrbStack/container was invoked. The #5156 lane remains request-only, and the shared coordination queue includes other live/requested work. A parallel #5598 Issue update reports zero A-failure support in the retained public six-task GUI pair. This package is a separate quantitative read-only look at #5424's synthetic paired potential outcomes; it neither supplies GUI support nor supersedes that `STOP_DATA` finding, and leaves the consumer's STOP unchanged.

