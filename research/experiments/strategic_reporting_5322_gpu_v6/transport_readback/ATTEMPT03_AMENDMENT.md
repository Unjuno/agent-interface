# Readback probe amendment — attempt 03

Attempts 01 and 02 remain STOPPED; their raw frames, checker failures and posthoc audits are preserved unchanged. Attempt 03 uses a new payload pattern (`z`) and a corrected, quote-safe independent length/hash/JSON checker. It is a new synthetic test, not inference replay.

One 13,449-byte JSON payload is sent over PTY. The controller writes the framed bytes once, records immediate GitHub readback, polls only reads for up to 30 seconds if needed, verifies exact frame bytes and an independent decoded payload SHA/length/JSON, commits both readback and audit records, then sends the matching ACK. No Ollama or model requests.
