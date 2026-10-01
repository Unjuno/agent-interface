# Python-Xlib 0.15 XGetImage String8 boundary

Issue #4638; successor to the unresolved historical-version question in #4455.

## Decision

PASS_X11_STRING8_PY015_BOUNDARY_SCOPED.

One frozen local Docker allocation completed all 30 scheduled cases. The raw-only independent audit passed with 18 checks and no errors; all 12 copied-evidence corruption controls were rejected. No runtime file was modified.

## H / T / D / C / U

H — Python-Xlib 0.15 may return str for valid UTF-8 String8 payloads, making bytes(image.data) raise TypeError; UTF-8 re-encoding should reproduce the native bytes, while byte payloads remain unchanged.

T — Python 3.11.16, python3-xlib 0.15, Debian 13, private authenticated TCP-disabled Xvfb in the frozen Docker image. Five deterministic 8x8 payload patterns × root/child drawable × three fresh repetitions = 30 first-outcome cases. No model, task input, user desktop, or GPU.

D — 30/30 completed; 12 str and 18 bytes; 12 legacy TypeErrors; candidate/native byte mismatches 0; fixture-pixel mismatches 0; independent audit errors 0; controls rejected 12/12. The frozen PASS gate is met.

C — This is one local Linux/amd64 Xvfb environment and synthetic drawable content. The root/child and repeated cases are directed boundary coverage, not a natural prevalence estimate.

U — No claim about semantic pixels, applications, freshness, model utility, latency/tokens, other versions, other platforms, production reliability, or runtime promotion. The auditor and corruption controls are separate from the runner/candidate, but are same-author checks, not external human review.

## Formal details

All six all-zero cases and all six ascii_and_utf8 cases returned str and caused the exact legacy TypeError. The ascii_and_utf8 pattern includes a valid multi-byte UTF-8 sequence. All six high_non_utf8 cases, six mixed cases, and six ordinary_color cases returned bytes. Every str re-encoded to the same bytes as independent native libX11 XGetImage; all bytes cases remained value-identical under normalization. Every pixel vector also matched the independently read native pixel vector.

There were 30 unique case IDs, 30 unique Xvfb PIDs, and 30 unique fixture PIDs. Every row completed; all fixture and Xvfb exits were 0; cleanup was complete 30/30; TCP listening was false in every case; and every private Xauthority file had mode 0600. The auditor checked all 30 rows, schedule identities, process/display receipts, geometry/stride, payload representation, byte hashes/lengths, pixel oracle, denominators, and raw SHA-256.

## Reproduction and retained evidence

Image digest: sha256:1c334ebd65f4b1bfe81cc84c90780ea01e6f70c0f7b18cd89c09e03406460238.

The formal command used the local image with network disabled, read-only root, CPU limit 4, memory limit 4 GiB, PID limit 64, a 256 MiB private /tmp tmpfs, and one writable output mount. The exact source, image, schedule, and gates are in the preformal FORMAL_FREEZE.json and are read back on the Issue branch before case 0.

Raw SHA-256: 0e39b0d1d29dfc413d842b9a1c2096f812b599d3cc11f301e1131a41ad6ab266.

The first audit/control invocation stopped before row parsing because the output bundle lacked the already-frozen schedule. The exact schedule was added, hash-checked, and the audit/controls then passed against unchanged raw rows. No formal rerun occurred; see AUDIT_ATTEMPTS.md.

## Integration boundary

This result validates the old-version representation hypothesis only. It does not authorize a production patch, close #4455's separate current-runtime compatibility question, rerun #4304, or establish runtime/product behavior. Keep the shared X11 backend unchanged.
