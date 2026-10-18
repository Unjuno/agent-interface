# Post-crash effect reconciliation bootstrap

## Issue #8900

**Status:** Open, unverified transfer and evaluation-method proposal.

**Idea.** After restart, an operation can remain `UNKNOWN_RECONCILE` because the external application effect may have occurred while its local receipt is absent, pending, or torn. Test whether an independently grounded, read-only evidence root can support a staged path to classify some cases without restoring task-action or retry authority.

**Relationship to prior work.** [#7802](https://github.com/Unjuno/agent-interface/issues/7802), [#7807](https://github.com/Unjuno/agent-interface/pull/7807), and [PR #8179](https://github.com/Unjuno/agent-interface/pull/8179) separate durable local state from external-effect truth and leave unavailable cases unknown. [#5970](https://github.com/Unjuno/agent-interface/issues/5970) studies recovery reachability from typed independent seeds. #8900 proposes their intersection: reachability of evidence for an in-doubt external effect, with authority unavailable until independent classification. These references are context, not proof that a real application exposes such a source.

**Proposed finite discriminator.** Compare local-bits-only classification, an always-UNKNOWN baseline, and a staged planner seeded by typed read-only evidence roots. Enumerate valid, stale, wrong-epoch, shared-fault-domain, cyclic/self-confirming, insufficient, contradictory, and unavailable roots. An independent raw-only auditor should reconstruct every path and classification. The candidate may not perform task input, retry, compensation, or application mutation.

**Decision boundary.** A method-scoped pass requires at least one independently justified resolution beyond always-UNKNOWN, zero false effect classifications, fail-closed handling of invalid or insufficient roots, and no restoration of action/retry authority. If there is no valid root, or the source cannot be specified independently, `UNKNOWN`/HOLD remains the correct outcome. A finite authored graph cannot establish real source independence, application truth, durability, exactly-once behavior, task correctness, or permission to retry.

**Current evidence:** No implementation, allocation, experiment, VM/power-loss test, or runtime change is reported. The issue explicitly frames a bounded no-model finite test as a proposal; the live application and real external effect remain untested. See [Issue #8900](https://github.com/Unjuno/agent-interface/issues/8900) for the full preregistration and provenance.
