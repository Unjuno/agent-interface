# Development notes

The first focused integration run failed its cancellation assertion: the bridge
made one immediate `input_state` request after the cancellation flag was set.
The owner thread had not yet serviced cancellation, so this request returned
while the key was still held; the owner then appended a verified cleanup record
shortly afterward. The failed candidate had no release receipt and retained
`F8` in bridge-held state.

The repaired candidate waits up to 500 ms for a new owner record when the step
finishes with cancellation set. It then issues a serialized `input_state`
barrier. Reconciliation still requires verified empty aggregate state and a
unique per-key record joined to the exact owner, key, intent, actuation ID, and
original program/step. The failed first run was during development of this
offline construction test; it was not a separate live or allocation run.
