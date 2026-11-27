# Selected backend / owned service cancellation boundary

Question: can current RPC v2 replace the selected in-process owner without losing
independent release when the actual Executor worker is paused after key-down?
Use three fixed ordinary construction cells: actual selected backend + Executor
with local owner paused/cancelled (positive control), external service with only
an owner_id metadata shim paused/cancelled, and external shim normal completion.
All display/query/input is Fake X; real private sockets/owned Python children only.

`test_owned_owner_executor_boundary.py` preserves events, actual service edge bytes,
initial source, parent cancellation/interruption, terminal, service identity/exit
and source pins. Pause the worker after the actual backend down RPC returns;
cancel through the actual Executor; inspect a fixed250ms window before resume.
It is a diagnostic window, not an asserted physical release bound. No new RPC
is sent during the window. Initial lease deadline10s prevents intended expiry
from explaining release in that window; retain timing to check that condition.

Decision: if remote held edge persists while local owner releases, reject direct
substitution and require an independently serviced cancellation relay plus cause
telemetry through the backend custody adapter. Normal completion alone cannot
qualify adoption. After resume, preserve actual final cleanup independently; no
failed early cancellation is upgraded. No production adapter/default is added.
Normal/-O run once per fixed source; preserve first output on failure. Saved-byte
readback and negative mutations, bounded review, verified main integration and#59
continuation complete this finite boundary audit. No new coordination Issue.
