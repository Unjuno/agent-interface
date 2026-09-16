# Development record

1. Exact retained preflight dependency was used unchanged.
2. Deterministic interposition was placed at the first `xtest.fake_input` only. The wrapper mutates the global X core map through a separately opened X connection, synchronously completes that change, records `mutation_done_ns`, then records `first_forward_ns` and forwards the original event.
3. Development results: no-mutation US control exact `@`; late German mutation produced `"`; late French mutation produced `2`.
4. In both changed cases the unchanged retained `deliver()` remained `accepted=true`, `error=null`, emitted four events, and verified physical release. Mutation completion preceded first forwarded input and final map hash matched the target map.
5. No closing mechanism was developed here because a separate Writer X11 server-grab serialization lane already exists. Stop tuning and freeze the negative discriminator.
