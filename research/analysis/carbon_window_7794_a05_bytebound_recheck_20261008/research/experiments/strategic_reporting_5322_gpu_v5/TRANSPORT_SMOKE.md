# v5 synthetic transport smoke evidence

No model inference was used. The hash-verified `capture_gpu_pilot_stream_v5.py` ran with `--synthetic-smoke` on the local interactive PTY using the frozen `row_frames.py` module.

For each call index 1–6, the runner emitted one 6,544-byte synthetic payload as 273 short frames. The controller validated frame ordering and the 78-character line bound, updated the corresponding `call-XX.frames` file through GitHub, fetched it back, verified byte-for-byte equality, and only then sent `ACK n`. All six GitHub writes/readbacks and ACK barriers completed. The framed final event (index 0) reports `SYNTHETIC_TRANSPORT_PASS`, six events, and zero model calls; its four frames (79-byte payload) were written and read back. The runner exited with code 0.

Files:
- `transport_smoke/call-01.frames` through `call-06.frames`
- `transport_smoke/final.frames`

Each synthetic event carries SHA-256 `fc5b471da2997f9059f0b01ce6df999821334226f9af58200c99e769b7cb0944`; all six payloads are identical by design. Unit tests additionally verified round-trip decoding, checksum rejection, missing/reordered/duplicate/corrupt frame rejection, and the reserved final-event ID.
