# Prepare input requests from received evidence

Actual self-use repeatedly copied observation sequence, delivery ID and absolute
deadline into handwritten JSON. prepare_program.py now builds those fields from
a received batch and explicit assistant-selected steps, program ID, lease_ms and
finish_after choice. It uses receipt_image.py to resolve the referenced image,
requires matching clock/terminal time and delivery references, and writes a new
command file without overwriting an existing one. It sends no input itself.

The deadline is still historical runtime time plus the explicit lease duration;
preparation neither refreshes observation nor renews input authority. Runtime
expiry, focus and admission checks remain unchanged. If the image clock and a
received clock disagree on sequence, preparation refuses instead of guessing.
This helper records producer=assistant and is intended for this assistant's
chosen programs, not unattended scripted benchmark attribution. Steps are copied
through strict JSON; their operation semantics remain runtime-validated.

Three recorded commands (initial Calc entry, Calc format confirmation and browser
draft replacement) are regenerated exactly, including all fields. Four negative
controls reject missing delivery, mismatched clock sequence, absent runtime time
and an oversized lease. These are known inputs, not held-out performance tests.

The assistant then used it live on private X11 xterm seed 991030. After viewing
the receipt-selected image, it specified only text t991030 and Return, program
ID and a 30-second lease. The preparer generated the runtime evidence fields;
the caller obtained read cursors from responses. The program was accepted before
expiry and saved the expected token. Outcome client returned evaluated=true.

| Metric | Measured |
|---|---:|
| First capture to outcome client return | 36.649 s |
| Initial socket return to admission | 16.271 s |
| Local program | 280.669 ms |
| Outcome client wait | 96.591 ms |

Audit verifies one submit, three exact frames, release, request lineage, the full
eleven-record prefix, saved token and exact regeneration of the actual prepared
command. No rejection or status fallback occurred. Runtime exited zero. Compared
with the earlier simple-token episode's 36.125 s, there is no observed total-time
improvement. Seeds differ and runs are sequential/uncontrolled, so neither causal
speedup nor regression is established. Manual field transcription is removed;
network exchanges, model input tokens and costs are not shown to decrease.

This is a preparation component, not a fully unified send/receive client. Source
batch paths, step files and transport invocation are still explicit. Requiring
readable image files is a local research constraint. No atomic freshness or
durability guarantee is added. Next consolidate the caller's actual invocation
path and measure its outer overhead, instead of attributing subsecond runtime
improvements to the whole task.

Evidence: results/prepare-program-01, results/prepared-self-use-01 and
results/prepared-self-use-audit.json. Probe and live audit source manifests are
retained. No default promotion or human-tempo claim.
