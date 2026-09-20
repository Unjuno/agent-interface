Issue #3676 local Docker audit reproduction

H: The frozen #3675 audit accepts contradictory/non-canonical event traces and its documented CLI invocation fails.
T: Preserve #3675 raw/freeze/audit/source unchanged. Run the frozen auditor in a fresh local Docker container with network disabled and read-only input. Probe unexpected event, duplicate stale row, contradictory bridge flags, reordered transitions and unsupported field; invoke documented CLI shape once.
D: Record hashes, baseline result, every mutation result and CLI status. This probe reproduces the defect; it does not supply or accept a hardened auditor.
C: Local Docker Desktop 4.91.0 / Engine 29.8.0, python:3.12-slim, linux/amd64, network none, read-only source/evidence mount. No GUI/X11/model/input; no retry.
U: Five finite controls do not characterize every possible auditor weakness or alter the scope of the original X11 run.

Result: FAIL_AUDIT_CONTRADICTORY_MUTATIONS_ACCEPTED; STOP_CLI_USAGE_ERROR. See RESULT.json. Original frozen files remain byte-identical. This is not a rerun of the X11 allocation.

Reproduce from repo root:
```powershell
docker run --rm --network none --read-only --tmpfs /tmp -v "${PWD}/research/live_control/x11_xres_incarnation_guard_3555_v2:/input:ro" -v "${PWD}/research/integration/issue_3676_docker_audit_probe_v1:/probe:ro" python:3.12-slim python /probe/reproduce.py
```
The script uses only the Python standard library and writes mutation copies only to temporary/container-local storage.
