# Attempt 01 STOP — audit harness assertion error

The synthetic PTY sender emitted one valid JSON payload of exactly 13,449 bytes, framed into 561 data frames. The GitHub write completed and a later readback exactly matched the frame stream; the controller reached the independent decode step.

The independent checker then stopped because its hand-written expected JSON value length was wrong (it expected 13,438; the actual payload string length is 13,435 after the JSON prefix and suffix). The controller sent `STOP`, not `ACK 1`. This was a synthetic-only test: zero model requests and zero inference calls.

After the stop, the stored frame file was re-read and independently decoded with the corrected length calculation. The byte count, embedded SHA-256, JSON validity and 561-frame sequence passed. The initial-fetch-versus-delayed-fetch timing was not retained, so this attempt does not establish when readback first converged. Preserve the checker failure; do not relabel it as a pre-ACK PASS.
