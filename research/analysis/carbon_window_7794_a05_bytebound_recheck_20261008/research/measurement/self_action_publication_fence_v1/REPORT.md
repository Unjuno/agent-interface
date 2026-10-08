# #1490 self-action publication freshness fence — retained formal result

Task: `SELF-ACTION-PUBLICATION-FRESHNESS-FENCE-20260918-001`

Decision: **`PASS_SELF_ACTION_PUBLICATION_FENCE_SCOPED`**.

## Question

#475/#498 showed that a controller-authored relevant action receipt can invalidate an older visually aliased target observation at a near-immediate boundary. #509 corrected the timing claim: that incremental protection was observed only about 4 microseconds after the action; at a true roughly 120 ms boundary the visual guard itself had already updated and self-action history added no incremental correctness.

This successor preserves those results and tests the role demotion proposed by #701: a self-action receipt is **temporary negative evidence while post-action publication is not yet fresh**, not permanent semantic identity.

The candidate binds every observation to the highest runtime-owned self-action sequence it explicitly covers. A newer relevant self-action invalidates older target evidence until a fresh publication covers that sequence. Once fresh evidence covers it, history alone no longer blocks a positive current guard.

## Construction history

The first directed construction is retained as `FAIL_CONSTRUCTION`. Two fail-closed controls (`FUTURE_COVER` and conflicting duplicate evidence) had identical candidate/oracle state and effect behavior, but the comparison harness incorrectly treated independent exception strings as semantic mismatches. No candidate scientific logic changed.

Construction v2 changed only comparison infrastructure: independent fail-closed errors are compared by canonical class, and the negative `VISUAL_ONLY` discriminator received correct duplicate-action bookkeeping. The same candidate then passed all ten directed categories; malformed controls rejected 4/4. Both construction outcomes remain retained.

Mandatory remote readback also found one comment-only `runner.py` transfer difference before formal. Remote executable bytes were adopted as canonical and local bytes normalized exactly. Seed, corpus, gates and executable semantics were unchanged.

## Frozen formal

One deterministic formal invocation, seed `149020260918001`, reruns/replacements/tuning `0/0/0`.

- histories: **240,000**;
- candidate/oracle result+full-state mismatch: **0**;
- publication-gap stale effects: **0 / 50,000**;
- stale-covered-publication effects: **0 / 30,000**;
- fresh-negative publication effects: **0 / 40,000**;
- fresh-positive publication effects: **40,000 / 40,000**;
- irrelevant-self-action false refusals: **0 / 25,000**;
- ordinary-authority-false effects: **0 / 15,000**;
- wrong-scope effects: **0 / 10,000**;
- future-covered evidence accepted: **0 / 10,000**;
- duplicate-action double advances: **0 / 10,000**;
- conflicting duplicate-evidence acceptance: **0 / 10,000**;
- `VISUAL_ONLY` stale effects on the two stale-publication families: **80,000**;
- `ALWAYS_HISTORY` false refusals on fresh-positive controls: **40,000**.

The paired discriminator results are the key outcome. Ignoring self-action publication lineage admits every stale positive guard in the frozen lag/stale-cover families. Conversely, treating relevant action history as permanent identity rejects every fresh positive post-action publication. The publication-bound candidate avoids both errors in this synthetic contract.

## Integrity

Independent audit: `PASS_SELF_ACTION_PUBLICATION_FENCE_SCOPED`; integrity errors `[]`. All eight copied-result corruption controls reject their mutations. Postformal source SHA-256 and Git blob identities match the frozen remote source.

- formal result SHA-256: `375b257a2f155e62fdc31964f7e6671ce25c52deb94cd1edd3fd2813d0b2dc74`;
- retained gzip/base64 result SHA-256: `4c6c03a9d123b0c7e55127db4a527e3f46edd381b133c3d89f801d5d7868a7b8`;
- audit SHA-256: `4a74e9de89bc24f61cf922046db9f22cdb6b7f632b3efa6208103c0ae1dbacc0`;
- deterministic ledger SHA-256: `a6ee454f96b99e2c0695a9df6e3048f90efa8514ac7ce01c112ec65eefeee2a5`.

Earlier compressed construction uploads are retained as non-canonical transfer artifacts because exact byte validation was not established after upload. Canonical construction evidence is the compact remote-readback summary, v1/v2 audits and the raw local JSON SHA-256 identities recorded before formal. This limitation does not affect the frozen formal source or result.

## Interpretation

The result supports a narrow role for self-authored action history:

`relevant self action -> publication not yet covering it -> invalidate older target evidence`

and then:

`fresh publication covers action sequence -> evaluate current evidence normally`

It does **not** make self-action history a target identity mechanism or action authority. Ordinary authority remains separate.

## Boundary

Synthetic publication-lineage semantics only. No Inkscape rerun, natural GUI paint/publication-lag rate, external/user mutation coverage, model benefit, task latency, token saving, or production-runtime promotion claim. An external or unreceipted mutation remains outside this mechanism and still requires current evidence/other provenance.
