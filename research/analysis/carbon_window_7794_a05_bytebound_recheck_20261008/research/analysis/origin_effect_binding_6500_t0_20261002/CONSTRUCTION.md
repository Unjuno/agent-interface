# Construction checks — before formal freeze

The first host construction suite had 2 failing assertions. Inspection showed the `omit_embedded_origin` mutation was applied to a legitimate baseline whose embedded-origin field was already `None`, making that mutation a no-op. No formal candidate/auditor/container had run.

Before freeze, the mutation challenge was changed to start from the declared `UNTRUSTED_EMBEDDED_CONTENT / ORIGIN_BOUND` row, while the similarity-score inversion starts from the high-risk legitimate similarity-alarm row. All other frozen cases, policies, decision gates, row count, and mutation classes were unchanged. The corrected host suite passed 8/8. The corrected construction suite then passed 8/8 in a separate disposable OrbStack container. This is a preformal harness correction, not a formal allocation retry.
