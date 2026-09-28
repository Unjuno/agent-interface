# Retained workload accounting

The read-only `runtime.integration_checks.workload` module first validates the existing host timeline and reply hashes, then counts tool calls and explicit public dispatch receipts. A returned MCP response is not a completed action. Completed, refused, execution-failed, relay-refused-before-dispatch, unknown and missing replies remain distinct. Unrecognized or conflicting public receipt shapes are unclassified. Release verification and inspection errors remain separate per-call fields.

| Historical trial | Total calls | Reported completed dispatches | Reported refused dispatches |
|---|---:|---:|---:|
| Calc with bundled inspection | 7 | 3 | 0 |
| Child-target inspection failure | 5 | 2 | 1 |
| Managed-target inspection | 4 | 2 | 0 |
| Child ancestry plus prefix repair | 7 | 3 | 1 |

These are different tasks/builds, not a matched performance comparison. The last row includes the initial input, one visually chosen prefix repair and save; the counter cannot know that the second completed action is a repair. The explicit primary review, passive event log and independent saved effect are retained in `../managed-target-ancestry-01`. Do not infer task correctness, input replay, semantic recovery cost or input neutrality from counts alone.

Reports carry per-call completed presentation/review counts, the existing host-time partition, and hashes of their inputs. A partial timeline stays partial and contributes unknown outcomes for sends without replies; no reply is not proof of zero input. This does not measure first useful model feedback, semantic completion, isolated model waiting, actual model tokens/fees or human tempo.

Run `python3 -O runtime/results/retained-workload-01/verify.py` to reconstruct all four inventories from the already archived host records and compare the exact reports. It writes only temporary copies of flat host records, dispatches nothing, and leaves the original bundles unchanged. The source bundles retain errors and interrupted allocations; this inventory covers the four completed host lifetimes, not the interrupted allocation without a host.
