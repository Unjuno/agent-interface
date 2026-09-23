# Native Docker integration 2558-v2

This is a local, model-free vertical-slice result for successor Issue #2558. The repo at main was mounted into a locally built Docker image (`agent-interface-golden-local:20260920`) with Python 3.11, Chromium, Xvfb, Pillow, NumPy, python-xlib and jsonschema.

## H/T/D/C/U

- **H:** the public native bridge can execute a freshly observed, guarded text/save action in the local Docker X11 environment, verify the independent effect, and refuse reuse after focus invalidation.
- **T:** one Chromium-free private fixture allocation; native artifact capture, handle bridge, read-only continuation and controlled focus-change probe enabled. No helper or primary model calls.
- **D:** independent effect `saved=true`, exact text `docker2558`; action-to-scored-effect `242.615 ms`; visual target revalidation true; stale program refused; focus-change reuse refused with `emissions_delta=0`; verified release present.
- **C:** this is not the six-task integrated comparison, not model/token/latency evidence, and not a general reliability claim. The initial attempt was retained separately as `NO_INTERACTIVE_DISPLAY` because the parent process did not inherit the private display.
- **U:** use the fixed private-display propagation in `runtime/native_result_self_use.py` as the prerequisite for the next local Docker integration allocation, then connect the existing model-boundary adapter and run the preregistered cold/warm/invalidation/repair workload.

The independent application effect remains the task-success oracle; adapter program completion is not promoted to task success.
