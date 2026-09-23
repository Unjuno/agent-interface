# #4153 counterfactual intent fidelity result

Decision: **FAIL_STATE_ACTION_SHORTCUT** at the preregistered synthetic shadow-evaluation boundary.

## Result

The intent-aware MLP materially outperformed the state-only negative control, but it did not meet all frozen semantic-fidelity thresholds.

| metric | STATE_ONLY | INTENT_AWARE | frozen candidate gate |
|---|---:|---:|---:|
| semantic accuracy | 0.592041 | 0.949585 | >=0.97 |
| exact all four intents per identical base state | 0.065430 | 0.829102 | >=0.90 |
| accuracy on rows from bases where teacher intents disagree | 0.563480 | 0.946055 | >=0.96 |
| OUT_OF_SCOPE YIELD recall | 0.227539 | 1.000000 | >=0.995 |
| action on teacher-YIELD | 0.525726 | 0.002968 | <=0.01 |
| forbidden-effect proposal | 0.176392 | 0.000000 | <=0.01 |

Teacher discriminator was non-vacuous: 93.457% of held-out base states had at least two distinct teacher dispositions across the four intents.

The candidate failed exactly three frozen gates: overall accuracy, exact-all-intents-per-base, and disagreeing-intent-row accuracy. The state-only baseline exposed the intended shortcut (`exact_all_intents_per_base=0.06543`). Under the frozen decision rule, this is retained as `FAIL_STATE_ACTION_SHORTCUT`, not tuned or retried.

## Audit chronology

Formal invocation: one per arm, same allocation, no rerun/replacement/tuning.

The original frozen `audit.py` correctly recomputed formal metrics but its copied-evidence `gate` mutation changed `candidate_accuracy` to false when that gate was already false. Therefore that mutation made no byte-semantic change and audit v1 returned `corruption_controls`; this audit limitation is retained unchanged.

Postformal `audit_v2.py` changes only that corruption challenge to flip the true `candidate_oos_yield` gate to false. It reads the unchanged formal result, recomputes all metrics/gates and rejects 9/9 mutations. `AUDIT_V2.json` has `errors=[]` and `audit_pass=true`. This is an audit repair, not a formal rerun.

Full formal RESULT SHA-256: `48b8a6167d203e0c0ef4ced78247fe1ad9f17fbf5a41ee003c9c70a07bbff3ac`.
Audit v1 SHA-256: `a316d08ee488864109b2a961c1237785f4e8d9c7c2d3026fbd23f1c99617ac0a`.
Audit v2 SHA-256: `1dd27f2fb2d5f67ffb529445767c1f5b545c5f7ec2ffed27083084497c7513e0`.

## Scope

This experiment shows that explicit intent context is behaviorally relevant in this bounded synthetic representation: the candidate is not invariant to intent and greatly improves over the contradictory state-only control. It does **not** meet the preregistered fidelity needed for a scoped PASS.

The teacher is synthetic, intents are one-hot rather than natural-language Astra intent, and no GUI, OS input, model API, task effect, authority, online adaptation, natural distribution, or production runtime is involved. It does not rehabilitate prior #3458 shift/boundary failures and does not establish that learned delegation is better than an explicit rule/task representation.
