# Issue #5455 synthetic large-frame readback probe

## H / T / D / C / U

- **H:** The v5 live call's first frame readback mismatch was either a transient GitHub read-after-write response or a controller comparison defect. A later fetch exactly matched deterministic regeneration from the recovered call.
- **T:** Send one valid JSON payload of exactly 13,449 bytes through the frozen `row_frames.py` over the local PTY. Expected encoding: 561 ordered data frames, length and SHA-256 headers, ASCII lines at most 78 characters. Create one GitHub frame file, compare the immediate fetch byte-for-byte, and if necessary repeat read-only fetches once per second for up to 30 seconds. Only send `ACK 1` after exact readback and independent local decode/hash/JSON verification.
- **D:** PASS if the saved frame file becomes an exact byte match within 30 seconds and independently decodes to the original 13,449-byte JSON payload; record immediate mismatch and convergence delay if any. STOP if no exact match arrives or the decoded payload/checksum differs. No model requests or inference.
- **C:** Windows host, Python 3.11.9, GitHub MCP Contents API, interactive PTY. No Ollama use, local disk output, config change, or network inference.
- **U:** This tests one synthetic payload and one GitHub path. It does not establish read-after-write behavior for every repository size, endpoint, or backend, nor a model/GPU result.

Frozen SHA-256:
- probe `large_frame_probe.py`: `15837e13c5bfcf0403d58568cc43545e0f91c198750eb4c83a45f745cd1cee92`
- reused decoder `row_frames.py` from main: `982034983289a7c2d5403eae355e148920d64b4fa6f2efa42bc6ba8fad490df1`
