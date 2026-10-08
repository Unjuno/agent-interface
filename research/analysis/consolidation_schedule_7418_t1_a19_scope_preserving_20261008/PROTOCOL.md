# T1-A19 protocol (prepared; formal freeze pending runtime qualification)

## Question and changed factor

Does consolidation cadence still change answer accuracy or evidence faithfulness on a second GUI-like corpus when every derived claim preserves app/mode/surface scope and the answer oracle sees only the evidence visible to that schedule?

A16's PASS_METHOD remains valid for its frozen value/source mapping. Its raw-only scope audit showed that effect claims omitted applicability context, while its query oracle used the contextual source ledger. Its aggregate contrast was dominated by one hand-authored common-save question. A19 changes corpus, claim schema/prompt, and query scoring protocol together to remove those limits. Within A19, cadence remains the only randomized treatment; the four schedules receive identical ordered episodes, query batches, model, decoding, and prefix checkpoints. A19 is not pooled with A16 and cannot estimate which individual protocol correction caused any difference from A16.

## H / T / D / C / U

**H — hypothesis.** On this finite second corpus and fixed model, per-episode, batch-2, terminal, and episodic-only schedules produce at least one same-direction, practically material paired-seed difference in exact query answers after a clean transition audit. If no such difference appears, schedule sensitivity is not demonstrated under this scope-preserving, visible-evidence protocol.

**T — test.** Freeze the six ordered evidence episodes, ten query items (two separately authored items in each of five families), prompt/schema, query batching, runner/auditor, seeds, model digest, decoder settings, and thresholds before inference. Run three fresh seeds across four arms and six prefixes. At every prefix, send five fixed query batches, each containing two items from one family. Consolidate after every episode, every two episodes, or once at the terminal prefix for the respective derived-memory arms. The episodic arm receives only its visible episode prefix. The independent auditor derives answerability from each raw request's visible evidence; it never uses hidden ledger entries to assign a summary-arm answer.

The frozen call plan is 360 query-batch calls plus 30 consolidation calls, 390 total. It yields 720 separately scored answer items. Repeated prefixes are correlated observations, not independent samples. Record model tokens and durations for every call, visible evidence bytes for each query batch, exact query-family outcomes, and every prefix. No GUI input, live user data, external effect, or writeback is used.

**D — decision.** `FAIL_METHOD` if the complete raw fails the source/value/scope transition reconstruction, query-visible-evidence check, identity/decode check, row-count gate, or corruption controls. Only a complete, error-free candidate exit is eligible for one auditor invocation. On a clean `PASS_METHOD`, return `OBSERVED_CADENCE_CONTRAST_SCOPED` if at least one pairwise schedule accuracy contrast is at least 0.10 in absolute value in each of the three seeds and has the same direction in all three. Return `NO_10PP_CONTRAST_OBSERVED_SCOPED` only if every per-seed pairwise contrast is below 0.10. Otherwise return `UNCERTAIN`. These labels describe only the finite observed fixture; they are not significance tests, equivalence tests, or evidence of a general cadence effect. The preregistered numerical threshold is unchanged. An incomplete or failed candidate is `STOP/INCOMPLETE`; preserve raw and do not retry or audit it as a complete allocation.

The separate pre-freeze gate calibration in `decision_gate_calibration_20261008/` found 34.65% detection probability for a simulated +0.10 arm difference under independent answers (Monte Carlo SE 0.11 percentage points), and a 43.68% sensitivity-decision rate under a perfect-prefix-cluster equal-accuracy null (SE 0.11 percentage points). Because the repeated prefixes are not independent, do not interpret an observed sensitivity label as a statistical or generalization claim. The calibration is an idealized model, not an estimate of Qwen3 behavior.

**C — competing explanations.** Any contrast may depend on this hand-authored corpus, query wording, the fixed two-question batch composition, different memory lengths/token use, or the chosen model rather than cadence generality. Batched query items may influence each other's response even though batch membership is fixed across arms. Scope preservation may remove an A16 artifact without eliminating other schedule effects. A no-contrast observation is not equivalence; it only says that this allocation's observed per-seed comparisons stayed below the registered threshold.

**U — limits.** The corpus is synthetic and small; two questions per family are not two independent corpora. Six prefixes and three seeds do not establish long-horizon stability, real GUI behavior, exception prevalence, user benefit, production safety, or optimal cadence. A model/schema-constrained claim audit does not demonstrate task effects. A16 and A19 use different protocols and are not pooled.

## Frozen implementation conditions

- Allocation: `GUI-MEMORY-CONSOLIDATION-SCHEDULE-8406-T1-A19-SCOPE-PRESERVING-20261008`.
- Model candidate: Qwen3 14B Q4_K_M, exact digest `bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8`; a fresh preflight must verify local tag/layers before any call.
- Seeds: 5801, 5802, 5803. No substitutions.
- Schedules: `episodic_only`, `per_episode`, `batch_2`, `terminal`; prefixes 1–6.
- Decoding: temperature 0.2, top_p 0.9, num_ctx 8192; query num_predict 512, consolidation num_predict 4096; thinking disabled.
- Candidate creates raw with exclusive-create mode and flushes each complete response. No retry path; interrupted or partial output is retained as STOP/INCOMPLETE.
- Before candidate invocation, `preflight.py` must verify the exact local model tag and that every manifest layer exists at the declared size. It performs no pull or inference. Candidate independently requires an unloaded private model before row 0 and checks tag/running identity before and after each request.
- Auditor is offline and reads raw only. It must not contact the model endpoint.
- Intended host is macOS. The experiment requires an isolated OrbStack Docker environment when eligible. The Docker Engine `_ping` timed out on 2026-10-08; no image digest/runtime preflight is currently frozen, so this protocol is prepared but **not formally frozen or authorized for inference** until the runtime/image and resource preflight are recorded.

## Construction gate

Before the formal freeze, run the deterministic construction suite and a mock candidate/auditor round trip. Require exact 390-call/720-answer counts, complete scope in every claim, visible-evidence-only scoring, delayed conflict creation, rejection of context deletion, and one-shot raw creation. Construction results do not satisfy T1 and do not authorize model calls.
