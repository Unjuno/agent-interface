# Formal allocation result — #4835

## Disposition

`PASS_DOCKER_CAPTURE_VISIBILITY_REPRODUCTION_SCOPED` for the predeclared single-image Docker/Xvfb replication only. This result does not supersede #4365 or establish general toolkit/runtime behavior.

## Formal execution

- Allocation: `capture-visibility-docker-4365-20260927-02`.
- Frozen code commit before formal: `6a231e972f0e0e9f7db5413d4d787cd5162a4ec6`; readback SHA for all seven protocol/source files matched.
- Image: `sha256:acf83a1dfafd43c44d81e2f28f85fc844fa43dc73f36b689a862dd924f9235d0` (linux/amd64, CPython 3.11.16, Python-Xlib 0.33).
- Producer container: `capture-visibility-4835-formal01`; exit 0, no OOM, network none, read-only root, 1 CPU, 1 GiB, 64 PIDs.
- Ordered schedule: six conditions × two fresh Xvfb servers = 12/12 COMPLETE; 24/24 capture attempts; zero capture errors; 4 CLEAR and 8 UNKNOWN policy results.
- All 12 Xvfb servers exited 0; all display sockets and per-case Xauthority files were removed.

## Independent raw audit and auditor correction

The originally frozen independent auditor `audit.py` ran once and returned `FAIL_RAW_AUDIT` for four child-covered parent-window captures. This finding was preserved. Read-only Docker pixel diagnosis over the same immutable raw files showed CHILD_HALF was exactly 4,800 parent-color + 4,800 child-color pixels and CHILD_FULL was 9,600 child-color pixels in both root-screen and window-client captures. The v1 auditor incorrectly required the full window-client drawable to remain parent-colored under direct children.

An additive, versioned `audit_v2.py` corrected only that raw-pixel expectation to the preregistered child geometry and fixed child color. It did not rerun or alter producer/source/case/raw outputs and retained all original source, digest, count, assessor, root-composition, cleanup and provenance checks. The auditor-v2 source and rationale were published/read back before it ran. It returned `PASS_RAW_AUDIT`, errors=[], checked 12 sessions, 24 captures and 24 image planes. Both audit versions and logs are retained.

## Scope

Evidence supports only this exact local Docker image, Xvfb version, fixed opaque layouts, and the unchanged #4385 adapter/policy. No claim about compositor/alpha/Shape/offscreen/mixed-depth/concurrent behavior, arbitrary toolkit, natural failure rate, runtime promotion, model/task success, or product performance.
