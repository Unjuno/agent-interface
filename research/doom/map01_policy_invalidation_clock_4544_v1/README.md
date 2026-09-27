# Issue #4544 enriched invalidation receipt regression

This additive successor tests the production-shaped monitor receipt that #4536
failed to model. It requires the semantic fields but preserves every additional
monitor field, adds explicit host/runtime clock domains, and retains all three
same-session probe samples. The historical decision-8 clock probes are real;
the missing invalidation timestamp and receipt values in the fixture are
synthetic and do not establish the predecessor's exact causal event.

The deterministic test is not formal gameplay. A fresh zero-model runtime
preflight and one newly preregistered formal allocation are separate gates.
