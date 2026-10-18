# C03 — cancellation arriving after the decision sample

## H / T / D / C / U

- **H:** In the additive v12 owner, if cancellation becomes visible after the `cancel.is_set()` value used to choose an explicit release cause has been sampled false, but before the corresponding key-up side effect, the recorded cause remains `release`. This is a narrower scheduling boundary than C01/C02, which make cancellation visible before the release-cause sample.
- **T:** Run one deterministic fake-Xlib owner-thread cycle against exact `origin/main` v10 with cancellation set immediately after dequeue, one against exact PR #7440 v12 with a separate Python thread making cancellation visible immediately after its false cause-sample, and one ordinary-release positive control against that same v12. Independently audit event order, key-up, owner receipt, and source hashes.
- **D:** C03 supports the residual-boundary hypothesis only if all three cases emit one KeyPress and one KeyRelease with a verified owner receipt; v10 and v12 both record `release`; the v10 cancel follows dequeue and precedes key-up; the v12 false sample precedes cancellation visibility and key-up; and the v12 ordinary control stays uncancelled with reason `release`. If v12 records `cancelled` under the post-sample ordering, the hypothesis is rejected. Any missing receipt, event, or provenance is STOP/FAIL rather than a pass.
- **C:** Cancellation cause may be defined at the owner’s sampled decision point rather than at the later key-up side effect. The barrier forces a single controlled interleaving between two Python threads and says nothing about how often it occurs under ordinary scheduling.
- **U:** Fake Xlib and an in-process thread only; no X server, physical key, GUI, model, game, task effect, recovery, or live/formal allocation. One forced cycle per source cannot estimate race probability or prove end-to-end cancellation publication.

This is an additive construction-boundary probe. It does not rerun C01/C02, alter their frozen evidence, or invoke a MAP01 allocation.
