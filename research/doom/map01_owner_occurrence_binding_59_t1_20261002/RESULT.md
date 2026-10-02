# Result — repeated explicit-up owner boundary

**Disposition: `PASS_OWNER_BOUNDARY_SCOPED`.** The pinned unchanged #5630
`InputOwner` completed two same-lease `W down/up` cycles through the fake
transport. Raw records contain two admissions and two explicit-up release
brackets in order, with the same owner/intent/keycode/key. Neither admissions
nor release brackets carries an occurrence ID. The fake transport observed
`KeyPress, KeyRelease, KeyPress, KeyRelease`; the only keymap query occurred at
terminal `close` and showed no remaining key down. Candidate and independent
raw-only auditor each ran once, exit 0; retries: 0.

Raw SHA-256: `7403f9ff7d091e1f174e2e1bd46ffa500e34b7f0ddb5ed88aeda3dbb4cf59ee5`.
Audit SHA-256: `5b230f2535e3e684ef674fe47d6b924f56443d1353f56ed938c051246baa635c`.
Frozen source/case hashes are in `SOURCE_HASHES.json`; output hashes are in
`RESULT_HASHES.json`.

## Interpretation

For this pinned owner revision and repeated explicit-up path, the current record
contract cannot directly associate the two admissions with their matching
releases using a per-occurrence ID. Nor does this path sample XQueryKeymap at
either explicit `up`; only terminal cleanup takes an empty-state sample. A
downstream adapter must not infer per-interval physical occupancy from these
owner/intent/key labels or the terminal sample. This confirms a source-record
boundary under a fake transport, not a live physical occupancy measurement.

This successor is separate from T0's immutable `FAIL_AUDIT`; T0's raw and audit
remain unchanged. It also does not answer the r133 live-control questions about
true held-input occupancy, independently useful feedback, bounded recovery, or
MAP01 outcome.

## Scope and environment

Windows CPython host; CPU-only in-process fake Xlib. No Docker container, real
X server, physical input, GUI, game, model, application effect, physical key
state, held-input duration, latency, or safety outcome was measured.
