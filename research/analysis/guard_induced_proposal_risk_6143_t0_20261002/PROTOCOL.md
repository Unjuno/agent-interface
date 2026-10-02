# Issue #6143 T0 — guard efficacy versus induced proposal mix

## H / T / D / C / U

- **H:** A correct guard's fixed-proposal rejection efficacy does not determine the guarded planner-plus-guard system's task-level harm when disclosure changes the proposal distribution. A complete opportunity denominator should distinguish compensation, null, and protective adaptation.
- **T:** Exhaustively enumerate three 1,000-proposal finite worlds: compensation, no adaptation, and protective adaptation. For each arm retain all proposed, rejected, harmful-admitted, unfinished and retry counts. Recompute guarded and unguarded arms on a shared fixed proposal policy as well as the adapted policy. An independently written auditor derives every metric from primitive integer counts and rejects frozen corruptions.
- **D:** `PASS_METHOD_SCOPED` only if the planted compensation world has 90% unsafe rejection sensitivity, zero safe false rejections, and greater harm per original opportunity for conservative/no-guard than aggressive/guard (5 versus 6 per 1000); the null preserves conservative proposals and yields 5 versus 0.5; protective adaptation reduces guarded harm below 0.5; all task denominators and refusal/retry counts reconcile; all corruption controls reject. Otherwise fail construction or method gate. No inferential or behavioral claim.
- **C:** Proposal adaptation may be absent or protective; task mix, guard policy, and classifier quality can all change net outcome. Fixed-proposal efficacy remains separately observable and does not stand in for adaptive policy performance.
- **U:** Authored integer rates, no sampling, no planner, no task states, no empirical risk, no temporal adaptation/habituation, no GUI/runtime/model, and no task or safety effect. No guard, permission, model, or live-study change is authorized.

## Frozen conditions

- Issue: [#6143](https://github.com/Unjuno/agent-interface/issues/6143)
- Source base: `e3a57eeef93153483d2ce40d2ef8050c89945fcc` (main at freeze).
- Candidate inputs and the primitive expected-count table are fixed in `fixture.json`.
- Candidate and auditor run once each after freeze; no retry. Auditor imports no candidate code and reconstructs expected summaries from fixed primitive counts.
- Intended isolation: deterministic Python standard library only. Docker Desktop Engine did not answer bounded API probes, so execution will be host CPython; this is not container-isolated evidence.

## Accounting

Every world has 1,000 original opportunities per arm and 1,000 proposals. The guard independently rejects 90% of unsafe proposals and 0% of safe proposals. Proposal-risk rates are represented as integer counts; the fixture uses unsafe counts divisible by ten. Rejected unsafe proposals are refusals, not admitted harms. An explicit retry count remains inside the original opportunity ledger and is not used to inflate the primary denominator. Harm is harmful admissions per original opportunity, never conditional on guard admission.

The worlds are authored counterexamples/controls, not empirical observations. The planted arithmetic does not validate Issue #6143's behavioral H; it validates that the proposed report separates conditional guard efficacy from an altered proposal mix.
