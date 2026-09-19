# Golden v3 CLI adapter P1 fix successor to #2303

This additive successor fixes two semantic-loss bugs identified in the merged
#2303 review:

1. nested runtime refusals are preserved as refusal diagnostics instead of
   being mapped to partial effect;
2. program completion remains independent from task success, including cleanup
   failure.

The fixture covers refusal, partial task after completed program, cleanup
failure, successful completion, and unknown status. It makes no GUI, model,
input, network, latency, token, or task-completion claim.

Reproduction:

    python audit.py
