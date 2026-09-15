# Semantic branch-predicate revalidation follow-up

Status: **RETAIN predicate-truth revalidation; reject both no-recheck and raw-value equality as general branch-validity rules.**

After establishing that branch selection must be revalidated at selected-action admission, this follow-up asks what must remain equal.

Minimal branch: `x >= 0` selects action A; `x < 0` selects action B. The selected action also has one independent admission guard. Initial `x` values -3..3, current `x` values -5..5, and guard false/true were exhaustively enumerated: **154 states**.

Ground truth says the old planned action remains branch-valid while the truth value of `x >= 0` is unchanged; raw `x` may vary within the same region.

| validation | stale executes | false rejects |
|---|---:|---:|
| no branch revalidation | **38** | 0 |
| exact raw value equality | 0 | **32** |
| **branch predicate truth equality** | **0** | **0** |

Thus the selected branch should generally be rebound to the semantic predicate that justified selection, not blindly to the exact underlying scalar/version when the method contract only depends on predicate truth.

This is consistent with the earlier typed-dependency result in PR #169, but now specifically closes the inter-phase branch-validity gap found in PR #193.

Next exact-runtime gate #197 should therefore carry a **plan-bound branch predicate receipt**, not merely a stale action name or exact raw resource equality, when the runtime can express that predicate safely.
