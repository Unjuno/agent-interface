# Readback probe amendment — attempt 02

Attempt 01 remains STOPPED because the controller's independent checker used an incorrect payload-string length constant. Its raw frames and posthoc audit remain unchanged.

Attempt 02 uses a new payload pattern (`y`, not `x`) and a sender that computes the expected JSON field length from the byte framing. It is a fresh **synthetic transport construction test**, not a model allocation or replay. One 13,449-byte valid JSON payload is framed, written once under a new path, read until exact equality (one-second read-only polling, maximum 30 seconds), independently reconstructed/hash-checked, and ACKed only after the verified readback report is committed.

No inference, Ollama API, model download, GPU call, or local file write is permitted.
