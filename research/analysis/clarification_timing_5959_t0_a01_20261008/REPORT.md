# Issue #5959 — T0 A01 result

**Disposition: `PASS_METHOD_SCOPED`.** The finite scheduling and audit contract
passed; the Issue's human interruption-cost hypothesis and T1 were not tested.

## Result

The candidate scheduled 15 frozen requests under three policies (45 rows). The
independent auditor reconstructed every row and the one mandatory-event bypass.
All 12 frozen audit gates passed, including the inclusive deadline boundary,
immediate zero-slack yield, cancellation on decision-version change, and no
modeled effect from stale, late, refused, unanswered, or unauthorized replies.
Five pre-freeze candidate-output mutations were rejected by the construction
auditor tests.

The authored finite cost trace demonstrates the intended method contrast in
C01: `low_cost_window` delivered at tick 6 with synthetic cost 1, versus
`immediate` at tick 0/cost 4 and `latest_safe` at tick 8/cost 5. These are
invented scoring values, not observations or estimates of human interruption
cost.

The fixture also exposes the tradeoff rather than hiding it. The immediate arm
has 8 modeled authorized outcomes, while each delayed arm has 5; the delayed
arms cancel four requests each when the decision version changes before
delivery. Three policy rows detect a reply beyond the frozen latency bound and
yield without effect. Those counts characterize only these authored traces;
they do not rank policies for people or real tasks.

## H / T / D / C / U conclusion

- **H:** Not evaluated. No human interruption measure exists in this T0.
- **T:** Completed the preregistered finite no-model event fixture in separate
  candidate and auditor containers; no GUI, participant, model, or production
  service was involved.
- **D:** `PASS_METHOD_SCOPED`: 15 requests/45 policy rows independently
  reconstructed; one hard event had zero modeled delay; zero-slack and stale /
  late / refusal / nonresponse / unauthorized-answer cases fail closed; the
  synthetic cost discriminator passed; and all construction mutation
  controls were rejected.
- **C:** The immediate policy can preserve an answer before a later version
  change; the synthetic lower-cost window may not predict experienced burden;
  latest-safe may be simpler and adequate. The fixture does not settle these
  alternatives.
- **U:** No human interruption, privacy, consent, perceived-control, answer
  latency distribution, end-to-end task effect, or runtime scheduling claim.
  T1 remains separately gated by explicit study authorization, voluntary
  participants, and independent outcome measures.

Exact hashes, raw output, audit, and the one-shot environment are retained in
[`FREEZE.json`](FREEZE.json), [`RUN_RECORD.json`](RUN_RECORD.json),
[`formal_01/RAW.json`](formal_01/RAW.json), and
[`audit_01/AUDIT.json`](audit_01/AUDIT.json). The independent audit and scope
limits are not evidence of a deployed policy or real-world benefit.

## Publication provenance

The formal run was executed against freeze commit
`751abbd3a891d44d1364a4d9b4d8d7e028796966`, based on main
`bfcc14e08fbfe5f2f04cd0237d13559e5d62538b`. Main subsequently advanced with
the separate #5826 analysis-index entry. This result branch was rebased to
preserve that entry; consequently its published freeze commit has a different
whole-tree hash. The 11 frozen experiment-package files were rechecked after
rebase and remain hash-identical (11/11, zero mismatches). No formal candidate
or auditor invocation was repeated.
