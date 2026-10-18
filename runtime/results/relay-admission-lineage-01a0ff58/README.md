# Relay admission boundary history rescue

This navigation record groups five additive historical evidence packages
recovered from `fix/relay-finite-json-01a0ff58-20261003`:

- [`relay-utf8-01a0ff58/`](../relay-utf8-01a0ff58/): strict UTF-8 pipe decoding and SDK-boundary observations.
- [`relay-unicode-scalars-01a0ff58/`](../relay-unicode-scalars-01a0ff58/): Unicode-scalar admission, retained receipts, and peer-SDK-boundary qualifications.
- [`relay-finite-json-01a0ff58/`](../relay-finite-json-01a0ff58/): non-finite numeric token refusal.
- [`relay-duplicate-json-01a0ff58/`](../relay-duplicate-json-01a0ff58/): duplicate decoded-key refusal.
- [`relay-deep-json-01a0ff58/`](../relay-deep-json-01a0ff58/): recursion-limit refusal and first-red history.

The 225 original files are copied byte-for-byte. Their individual reports,
source identities, raw records, and limitations remain authoritative for their
own scopes; this index does not combine their counts into a single experiment.
No producer, SDK probe, CLI archive, or historical allocation was rerun for
this rescue. Captured runnable archives and helper scripts are inert evidence;
do not execute them as part of ordinary validation.

These are retained diagnostics, not a claim that all cited code is currently
merged. Production code in `runtime/cli_v1/` is evaluated through its own
present-day tests and approval gates. The original #6879 implementation PR
remains separate because its current head has an explicit fresh-review and
native-platform validation gate.
