# Receipt-selected images in actual assistant use

The assistant used frozen socket v10 / interactive v26 to enter 532 and 590 in
Calc, save, inspect the format dialog, and confirm Excel format. The task, seed
991022, step arrays, decision references and one-clock deadline strategy match
receipt-clock-self-use-01. Runtime code is unchanged.

The initial CLI selection was inspected before opening its image. At the modal
boundary, a single functions orchestration invoked the existing socket read,
persisted the batch, ran receipt_image.py, parsed its relative_path, and opened
that path at original resolution. The assistant viewed the dialog before issuing
Return. No filename guess or failed image view occurred. This episode's modal
reference is 007.png, whereas the previous episode referenced 006.png.

| Measured interval | Prior episode | Receipt-selected episode |
|---|---:|---:|
| First capture to effect socket return | 61.548 s | 48.495 s |
| Initial socket return to first admission | 21.148 s | 17.081 s |
| Modal socket return to confirmation admission | 20.638 s | 13.540 s |
| Final terminal to early effect emission | 23.990 ms | 20.630 ms |
| Final terminal to independent evaluation emission | 37.539 ms | 34.725 ms |
| Early effect emission to socket return | 6.443 ms | 7.691 ms |

Both episodes used two programs, one clock and four socket calls before cleanup.
The new local program durations were 911.757 and 113.330 ms. All twelve AIT frames
match the referenced PNG pixels exactly; the saved workbook contains [532,590]
and its hash matches VERIFIED evidence. Both programs completed and released
input; no runtime rejection occurred. Terminal, effect and evaluation retain the
confirmation request lineage. Repeating the same request for the final read
does not write another confirmation. The full 23-record prefix is accounted for.
The process exited successfully after finish.

This is one familiar sequential episode per variant, with uncontrolled tool and
assistant timing. The prior episode includes its retained image-viewing mistake.
The shorter total is an observation, not a causal speedup estimate. Socket-return
intervals include model, orchestration, transport and admission; they are not
model-only reasoning times. Model receipt timestamps, actual input token counts,
cost, and comparable human timings remain unavailable. No default promotion or
freeze credit follows from this result.

Evidence: results/receipt-image-self-use-01,
results/receipt-image-self-use-audit.json and
results/receipt-image-self-use-comparison.json. The latter hashes the selector,
audit and comparison source. The audit verifies frozen runtime source hashes.

The next useful test is a new case requiring a different visible decision or
recovery, rather than repeatedly tuning this known two-program save sequence.
Keep all outer waiting and failed attempts in end-to-end timing.
