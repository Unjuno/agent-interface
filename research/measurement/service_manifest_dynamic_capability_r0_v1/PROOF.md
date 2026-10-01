# Separation proof

Assume one service/protocol epoch E has a byte-stability requirement for front-door manifest M, so for any t1,t2 in E, M(t1)=M(t2). Let mutable session capability state C(t) be encoded directly and faithfully in M(t).

Choose t1,t2 in E with C(t1) != C(t2). Faithful direct encoding requires the decoded capability value from M(t1) to equal C(t1) and from M(t2) to equal C(t2). Because C(t1) != C(t2), these decoded values differ; therefore their source byte strings cannot be identical under deterministic decoding. Thus M(t1) != M(t2), contradicting byte stability.

Conversely, if M(t1)=M(t2) is preserved despite C(t1) != C(t2), deterministic decoding yields one identical embedded capability value at both times, so at least one time is stale/incorrect.

Therefore a byte-stable front door cannot directly and faithfully encode mutable capability state across a capability change. A separate current object/reference (or semantically equivalent indirection) is necessary if both properties are required.
