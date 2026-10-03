# Caller attribution in host events

The existing relay host accepts optional caller-declared attribution in `send(tool, args, attribution)` and `sendPresented(tool, args, callbacks, attribution)`.

Required fields are `evaluation_id`, `phase`, and `model_stage_id`; `primary_call_id` is optional. Each supplied value must be a nonempty string of at most 128 characters. Extra fields are rejected. Phases are `setup`, `preflight`, `cold_acquisition`, `warm_reuse`, `invalidation`, `bounded_repair`, `subsequent_reuse`, and `termination`.

The host validates and copies these values synchronously before starting an attempt. It writes the copy as `caller_attribution` on `send_requested` and `reply_available`. Invalid metadata does not consume an attempt. Omission preserves the existing event shape. The transport request, tool arguments, presentation reservation, and review gates keep their existing behavior.

These values are caller declarations. They do not attest provider usage, establish a provider foreign key, grant input authority, or prove a task effect. Accounting consumers must retain actual provider records and explicitly join identities before allocating usage to phases. Missing usage and cost remain unknown. This feature neither repairs historical ordinal associations nor establishes a reduction in model calls, latency, or cost.

The regression is part of the existing `test_relay_host.mjs` entry. It uses the actual relay client with an inert stdio peer and checks copied event metadata, unchanged protocol requests, busy rejection, invalid metadata, and presentation. It does not exercise a live MCP SDK or GUI backend.

## Explicit primary commands

The existing primary stdio/exchange command envelope optionally accepts an `attribution` field beside `id`, `method`, and `args`. For example:

```json
{"id":1,"method":"call","args":["interface_clock",{}],"attribution":{"evaluation_id":"comparison-1","phase":"preflight","model_stage_id":"stage-1","primary_call_id":"call_actual"}}
```

The exchange copies the finite JSON request and validates attribution before consuming a command ID. Its existing primary caller receives a command-scoped host facade, which forwards this metadata only on actual `sendPresented` dispatches. Existing method arguments, policy checks, explicit close, busy rejection, STOP state, and command consumption after dispatch remain in force. No phase is inferred from the tool name. Metadata on a local review or presentation command does not invent a relay attempt or provider record.

Explicit attribution is retained in the exchange request and presentation record; omission preserves their existing shape. Each command must declare its own metadata; a subsequent command never inherits it. A null declaration means no host attribution. Shared validation is exported from the existing host module, preserving the portable two-file host/relay setup. Existing primary stdio needs no configuration or protocol version change.

New exchange and host regressions are included in their existing test entries. They exercise the real exchange/caller/host/relay libraries with an inert stdio peer, including invalid metadata before ID consumption, concurrent busy refusal, copied attribution, unchanged protocol request, and no next-command leakage. They do not establish live provider identity, model usage attribution, GUI behavior, or task/economic outcomes.
