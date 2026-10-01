# Publication transport note

The formal experiment and local evidence archive were complete before publication transport.

A first attempt to publish the complete Base64 archive as one `evidence.tar.xz.b64` file was read back as only 7,803 bytes (Git blob `cd1f037cd8c085957b085dc59eca65cc3ca33e5c`) and therefore did **not** match the local complete Base64 payload. That file is retained as `TRUNCATED_NON_EVIDENCE` and is never used by the reconstructor.

No formal case was rerun and no scientific source/result changed. Publication transport only was repaired by splitting the exact complete Base64 payload into five canonical parts. GitHub readback identities are recorded in `ARTIFACTS.json`; `reconstruct_evidence.py` concatenates only those five parts, strips transport whitespace, decodes them, and verifies archive SHA-256 `8998116524231673c2c7fdc1c333e078bb9a8980aeb0257dae03efe20a228dba` before writing output.
