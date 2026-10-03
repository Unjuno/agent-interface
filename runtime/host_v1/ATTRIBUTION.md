# Caller attribution in host events

The existing relay host accepts optional caller-declared attribution in `send(tool, args, attribution)` and `sendPresented(tool, args, callbacks, attribution)`.

Required fields are `evaluation_id`, `phase`, and `model_stage_id`; `primary_call_id` is optional. Each supplied value must be a nonempty string of at most 128 characters. Extra fields are rejected. Phases are `setup`, `preflight`, `cold_acquisition`, `warm_reuse`, `invalidation`, `bounded_repair`, `subsequent_reuse`, and `termination`.

The host validates and copies these values synchronously before starting an attempt. It writes the copy as `caller_attribution` on `send_requested` and `reply_available`. Invalid metadata does not consume an attempt. Omission preserves the existing event shape. The transport request, tool arguments, presentation reservation, and review gates keep their existing behavior.

These values are caller declarations. They do not attest provider usage, establish a provider foreign key, grant input authority, or prove a task effect. Accounting consumers must retain actual provider records and explicitly join identities before allocating usage to phases. Missing usage and cost remain unknown. This feature neither repairs historical ordinal associations nor establishes a reduction in model calls, latency, or cost.

The regression is part of the existing `test_relay_host.mjs` entry. It uses the actual relay client with an inert stdio peer and checks copied event metadata, unchanged protocol requests, busy rejection, invalid metadata, and presentation. It does not exercise a live MCP SDK or GUI backend.
