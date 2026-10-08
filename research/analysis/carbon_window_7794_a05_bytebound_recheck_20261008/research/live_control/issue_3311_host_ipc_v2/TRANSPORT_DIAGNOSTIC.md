# #3311 host IPC transport diagnostic v2

Status: `STOP_TRANSPORT_PATH_MAPPING_UNVERIFIED`; no model invocation, no GUI allocation, no task input.

This is an engineering setup diagnostic, not a #3311 formal allocation. The candidate design attempted to run the integrated desktop workflow in an OrbStack container with `--network none`, relaying model calls to a host Codex CLI via shared-volume request/response files. A pinned derived Linux/arm64 image was built from `mixed-formal-2992-debian:20260920@sha256:766abfd10382ab8b59ed793094a685481190f840d338b7bc4664ca162a2da619`; its Docker image ID was `sha256:e47cbddc70722a816758a4a1c27cf2a38071c889670be98bf3eacdc9fff17916`.

The derived image imports `jsonschema`, `Xlib`, `PIL`, and `openpyxl`; executables `Xvfb`, `openbox`, `wmctrl`, and Chromium are present. Six isolated unit tests for broker command construction and schema preflight behavior passed in this image. Python compile checks also passed.

The full OrbStack fake-CLI round trip did not pass. First probes exposed that host and container absolute paths are not interchangeable for OrbStack shared mounts; explicit mapping remained unverified, and a bounded fake-CLI round trip timed out before a broker response. Several test harness configurations were corrected during diagnosis, so none of those failed attempts are formal experiment samples. No actual Codex CLI/model command was started (`host_cli_invoked=false` in captured broker failures). The transport is rejected for use in this allocation until a simpler one-way mapping contract is independently verified.

No experiment result, success rate, efficiency metric, or product claim is supported. Preserve this record and these failed setup observations; do not replay this allocation. Next step is to stay within the existing Docker backend seam and determine whether its current explicit socket/IPC boundary can run with a current, independently verified preflight. If it cannot, issue a narrowly scoped successor before any model call.
