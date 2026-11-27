# Optional Win32 capture PNG artifacts

`configure_capture_artifacts(directory)` enables an optional PNG beside a Win32 capture. The image is encoded from the exact top-down BGRX buffer already used for the observation; the backend does not recapture or dispatch input. Metadata-only calls retain their original shape. The receipt includes the raw capture hash, PNG hash, dimensions, region and capture/encode/write timings. If PNG storage fails, raw capture metadata remains available with `artifact_error`.

The standard-library writer rejects non-integer/boolean dimensions, malformed buffers, either dimension above 8192, and images above 16,777,216 pixels before allocating the RGB rows. A successful file write does not prove display redraw, task effect, or durable filesystem synchronization.

The public stdio MCP live fixture packets under `research/integration/win32_public_mcp_live_effect_20261023_*` preserve the initial integration failure, the observer artifact result, task-effect outcomes, release receipts and limits. A single PASS is scoped to the tested owned fixture and host.
