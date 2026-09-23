# Content-bound claim readback after lost commit response

Task `COORD-GITHUB-CLAIM-READBACK-20260916-005`, Issue #368.

**Decision: `PASS_CONTENT_BOUND_READBACK_SCOPED`.** This is a narrow GitHub claim-registration outcome-recovery result. It does not establish authentication, simultaneous-request linearizability, a production lease service, or exactly-once execution.

## Why this rung

PR #367 retained a bounded stale-SHA re-read/recheck/merge mechanism and named one next question: a successful claim commit can become ambiguous if its response is lost. Re-sending blindly risks a duplicate or confusing another owner's semantically competing claim for one's own.

This experiment changes only the recovery observation: after one predeclared successful commit, the classifier receives the frozen candidate claim and one fresh GET of the register. The update response is retained only by the evaluator and is deliberately excluded from classifier input. No recovery PUT is permitted.

## Frozen identity

Publication BASE `fe0ef126a0e4b8604261c70e588dd522c9fefccb`.
Branch `research/github-claim-readback-fe0ef12`.
Pre-measurement HEAD `2ff8e897501aa434869bb19999b1e949d203c664`.

Frozen Git blobs:

- `policy.py` `e4960dac5363468dee1e50546783212b57ae006b`
- `plan.json` `7b4ca3bc2364bd7fc535a4a036c80c45b189a0f1`
- initial registers `298c8a310631a28989d79acb3ef2506ec7ba9031`, `84ff5a4746f459dbbf43dbe9607a330a7af7fc1f`, `2db52c7dc441a40d589431d4c1ac3cbdd4a31ddd`
- committed payloads `98109016cf098a290da64252792470d4e6e70bdb`, `f61f8695eabecf60de45883a2e40f05bb1d4b7f5`, `264b941319fdd9e9ef79765ee9309a828e2c54c3`

Canonical claim identity is the ordered tuple `(owner_nonce, task_id, scope, successor, question_key)`. `owner_nonce` is fixture metadata, not authentication.

## First measured outcome

Exactly three measured `update_file` calls ran, one per stratum. All three succeeded once. Each was followed by exactly one fresh GET. No recovery PUT occurred.

| Stratum | Commit | GET blob | Readback classification |
|---|---|---|---|
| identical self | `cc5edb280017fdc08d745edff00c776c871f049a` | `98109016...` | `ALREADY_REGISTERED_SELF` |
| different owner, same successor/question | `11cd6d2ca946c9929e04471f7872d80810ee33ec` | `f61f8695...` | `CONFLICT_OTHER_OWNER` |
| same owner, changed canonical content | `604003edf1de29cbe08bc45ea9b506145865d01f` | `264b9413...` | `CONFLICT_CONTENT_MISMATCH` |

Every GET blob exactly equals the pre-frozen payload blob for its case. The third stratum is the key negative control: owner equality alone is not sufficient for self-recognition.

## H / T / D / C / U

**H:** exact canonical content plus owner identity can distinguish a previously committed self claim from a competing owner and from changed content after the write response is unavailable.

**T:** three fresh GitHub register paths, three source-first-frozen payloads, fixed order, one successful commit and one GET per case, zero recovery writes.

**D:** all three commits and readbacks match frozen identities; classifications match the preregistered values; recovery PUT count is 0/3; decision `PASS_CONTENT_BOUND_READBACK_SCOPED`.

**C:** GitHub read-after-write behavior on this path may make the fixture easy. An unavailable/stale GET, real network partition, or uncertain owner identity would require a different fail-closed outcome. Exact curator-authored identity fields do not solve semantic paraphrase.

**U:** one repository/branch/connector and three sequential authored cases. Response loss is simulated by withholding the successful `update_file` response from classification; no actual transport fault is claimed. No simultaneous requests, performance/rate, fairness, authentication, lease expiry, or real experiment authority is tested.

## Evidence and verification

`result.json` retains all three initial GitHub commit SHAs, initial/payload/readback Git blob identities, classifications, zero recovery-write count and the explicit evidence boundary. `verify.py` is an offline deterministic checker over `plan.json` and `result.json`; it does not contact GitHub or start a new allocation.

The measured update responses are evaluator evidence only. The classifier's permitted input is the candidate claim from the frozen plan plus the single fresh GET register claim. Thus the experiment tests whether readback evidence is sufficient after an assumed lost acknowledgement, not whether the connector itself loses responses.

## Next single question

What happens when the successful commit response is lost **and the first readback is unavailable or ambiguous**? The safe default should not mint a second claim from elapsed time alone. A separate rung should compare fail-closed `UNKNOWN` against one bounded later readback without adding a write retry. Do not bundle expiry, authentication or production leasing into that first test.
