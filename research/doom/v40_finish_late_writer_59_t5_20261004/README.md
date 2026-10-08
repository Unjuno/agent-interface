# V40 late finish-writer completion accounting (T5, 2026-10-04)

## H / T / D / C / U

**H:** Once finish delivery exceeds its monotonic deadline, a later full-payload writer return after child termination must remain unconfirmed. It must not set `finish_sent` or imply graceful score completion.

**T:** Run the exact late-writer regression against PR head `a2ad677c78aab119eed65884af8848103a292b8c`, where child termination releases a blocked writer that then returns the complete finish payload. Preserve that baseline outcome. Run the same test against the candidate with a recorded deadline/completion timestamp, then run the complete V40 focused suite and independent audit.

**D:** `PASS_LATE_COMPLETION_NOT_CLAIMED` only if the baseline fails because it claims `finish_sent`, while the candidate records timeout and late completion, leaves `finish_sent` and `score_observed` false, retires its owned child, and passes the 12-test suite. Any late success counted as delivery fails.

**C:** The deterministic writer proxy makes the post-timeout completion ordering reproducible. A separate #59 Windows probe already demonstrated that a real 4-KiB blocked pipe writer can return the full finish payload after child termination; this test does not repeat that OS-level probe.

**U:** The result establishes source accounting under the stated boundary only. No game, model, GUI, physical input, formal allocation, verified application release, or task effect is tested.

## Change and evidence

The writer records when write+flush completes. `finish_sent` is assigned only by the caller after confirming that timestamp is at or before the monotonic deadline. A full-length completion after timeout remains flagged as late, triggers/retains owned-child retirement, and cannot become a graceful-success receipt.

`baseline-output.txt` preserves the first failing exact-head regression. `candidate-suite-output.txt`, compile/diff outputs, `RESULT.json`, and `SHA256SUMS` bind the repaired source and 12/12 focused suite. The earlier T4 pipe-backpressure result remains unchanged in its own package.


## Integrity follow-up (2026-10-05)

A fresh manifest check found that 13 of 14 entries matched, while the retained
`audit-output.txt` hash in `SHA256SUMS` did not match the committed bytes. The
manifest entry is corrected to SHA-256
`e05a824118e5e78e11111ae3d4bec7a226ccdd854f3b07c9fff61eb6409333e3`. The
output, candidate, tests, result, and first outcomes are unchanged. The
independent T5 audit still passes; this correction repairs package integrity
metadata only.
