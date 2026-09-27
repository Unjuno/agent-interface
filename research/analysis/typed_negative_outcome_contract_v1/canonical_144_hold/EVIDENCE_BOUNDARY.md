# Evidence retention boundary

The exact formal RAW/AUDIT bytes were present immediately after the one allowed formal invocation and their disposition/hash was posted to Issue #4174. They are no longer available in the current execution container after container reinitialization.

Do not reconstruct them by rerunning the consumed formal allocation. The retained SHA-256 is an integrity identifier, not a substitute for accessible bytes.

This path intentionally preserves the missing-evidence limitation rather than manufacturing a replacement artifact.
