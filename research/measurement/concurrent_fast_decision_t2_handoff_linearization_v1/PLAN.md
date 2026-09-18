# #1463 T2 handoff linearization

One factor: separate transport `raw_recv_return_ns` from the shared authority-publication linearization point `authority_publish_ns`.

H: final admission and publication serialized on one authority mutex yield zero admitted effects at/after publication, while R<C<P remains explicitly visible rather than being mislabeled pre-return.

T: directed real-thread construction plus independent pure-history oracle; after source freeze, one 250,000-history deterministic formal invocation at seed 146120260918013. No model/provider/network/GUI/X11/task input/shared runtime.

D: candidate/oracle mismatch0; post-publication effects0; R<C<P classification exact; invalid/replay/ordinary-false effects0; delayed-reported-receive discriminator exposes hidden-after-raw effects; corruption controls pass.

C: production can instead choose raw receive R as authority boundary only if R is made globally linearizable with final admission. This experiment does not prove R->P lag is operationally acceptable.

U: synthetic concurrency/measurement semantics only.
