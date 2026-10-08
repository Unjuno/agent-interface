# Bind completion to the admitted request, not the latest attempted label

Private interactive_v26 uses AdmittedLineage around ordinary Executor.submit.
Before submission it provides pending receive metadata. Only the executor's actual
accepted event freezes that metadata under the unique accepted action ID. The
pending context is cleared in finally even when validation rejects. Terminal and
final evaluation records copy the frozen admitted_request; unrelated later input
lines cannot rewrite it. Event socket v9 selects this entrypoint without changing
input authority, lease or underlying Executor v3 semantics.

The live probe sends two rejected concurrent attempts with action ID same-action,
then a valid submit using that same action ID and transport ID valid. Admission,
terminal and independent evaluation all carry runtime_request_sequence 5 and
transport_request_id valid. The two rejected attempts are receive sequences 2/3
in the opposite ordering from the prior cohort, and retain their own transport
identities without an admitted_request. Saved output is exactly t991024.

This tests real acceptance binding through the bridge/runtime, not attachment of
the most recently received command. Replay suppression, payload conflict and
reserved-field rejection controls remain in the probe. Audit validates source
hashes, three exact public AIT/PNG frames and owner close. Results are retained in
results/admitted-lineage-01 and admitted-lineage-audit.json.

The helper also has an effect_evidence attachment path, but this xterm run does
not exercise Calc's early effect event. It tags only accepted, terminal and final
effect/evaluation records; it does not establish full observation/input/effect
causality. Cancel request identity is intentionally not replaced with the submit
identity. Accepted bindings remain in memory for the session and are not bounded
or restart-safe. Direct runtime metadata remains caller supplied, not authenticated.
No default promotion or freeze credit.

Next validate the early-effect path and make request-scoped terminal reads consume
the admitted mapping explicitly. Keep rejected attempts distinguishable from the
request that actually acquired input authority; do not infer semantic success
from lineage alone. General performance/token comparisons remain outstanding.
