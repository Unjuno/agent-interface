# Pre-registration addendum — harness setup correction

Before any model request, the first harness launch failed at Python import
(`ModuleNotFoundError: docker_model_call_backend_v1`) because the disposable
script added the repository root rather than `research/live_control` to
`sys.path`. Inspection confirms it produced no IPC request, did not invoke the
host Codex CLI, and created no model response; this is a harness setup failure,
not an attempted experimental observation. No six-task action or GUI input
occurred. The partial empty attempt is preserved at
`attempts-live-v1/plain/` and is excluded from the registered outcome.

The only correction is the host harness import path. The frozen PR source,
prompt, model, container, schemas, call order, limits, and decision gates in
`PRE-REGISTRATION.md` remain unchanged. A new unique evidence directory
`attempts-live-v2/` will be used. The registered plain-then-compiled protocol
will now be attempted once. Any model/transport timeout, failed response, or
independent audit failure stops the sequence with no retry.
