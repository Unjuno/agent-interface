# Guarded Inkscape transfer 01: startup failure

Source 3152eb9d67bc7cd5913c0798b70be936bbc65f69. One original startup terminated with FileExistsError before any observation or input: the scaffold pre-created the bridge output directory while NativeHandleBridge requires exclusive creation. Remaining three planned cases were not allocated. Retained cleanup reports children terminal, but host_exit is null because the startup exception preceded the normal host accounting; the original tool handle separately returned exit 1. All recorded owned PIDs were absent at the subsequent audit.

The distinct [successor 02](../inkscape-guarded-transfer-02/README.md) removes only that caller directory precreation. This allocation remains a failed attempt. FROZEN.json preserves the original plan/code/schedule; the plan's per-key guard claim is corrected in [the final report](../inkscape-guarded-transfer-03/README.md), without rewriting the frozen plan.
