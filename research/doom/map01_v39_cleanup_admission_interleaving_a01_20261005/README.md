# V39 cleanup during admission return: bounded bridge construction check

This diagnostic tests the cancellation/cleanup race in PR #7805's fake-display candidate. The specific interleaving is: a down admission occurs; cancellation is set before the bridge's `owner.call("down")` returns; the InputOwner completes per-key cleanup and records its verified release; only then does the owner call return the admission receipt to the bridge. The candidate must emit admission before its contextual release receipt, end with empty owner and bridge state, and preserve the original actuation ID.

## H / T / D / C / U

- **H:** When owner cleanup completes before the down call returns, candidate V13/V2 keeps the admission context, emits one matching release after admission, and reconciles bridge-held state to the empty owner state.
- **T:** One bounded fake-display call-order injection against the exact PR #7805 candidate. A cancellation event is set inside the wrapper around `owner.call("down")`; it polls the fake owner's read-only state until both owned inputs are empty and a cleanup record exists, then returns the down receipt. No GUI, X11 server, game, model, provider, or physical input is used.
- **D:** Scoped construction PASS requires proof that empty owner state and one cleanup record existed before the wrapped owner call returned; emitted events exactly `input_admission` then one `input_release_measurement`; matching program, step, key, owner, intent, and actuation; verified sampled up; empty fake display and bridge-held state. An unproven boundary is HOLD.
- **C:** The owner state query and thread scheduling are synthetic fixture behavior; this is not evidence that a production runtime encounters the interleaving or that the candidate is deployed.
- **U:** One key, one fake-owner interleaving, one frozen candidate source. No application consumption, task effect, recovery benefit, live X11, gameplay, safety rate, latency, or MAP01 outcome is established.

## Attempts and disposition

A01 is retained as **HOLD / boundary not established**. It set cancellation before returning, but the sampled owner still reported F8 down. The probe incorrectly labeled its boolean `cleanup_completed_before_down_return`; the state record is authoritative and shows that claim was unsupported. A01 is not counted as reproduction or PASS.

A02 forced and observed the complete cleanup before return and passed at PR head `84148054938965dc245602e37220586e07c6f28e`. While packaging, PR #7805 advanced to `39264f167f8f7541aaf10c43d287938b1317f520`; its changes touched the bridge reconciliation-error path and added tests. A03 repeats the verified ordering on that updated head and is the current scoped result: **PASS_ADMISSION_RETURN_RACE_CONSTRUCTION**.

The A03 result shows owner state empty and one owner cleanup record before the wrapped down call returns, followed by an admission event and one matching contextual release. The final fake display and bridge ledger are both empty. Source hashes and independent checks are recorded in `FREEZE.json`, `SOURCE_LOCK.json`, `AUDIT.json`, and `SHA256SUMS`.

## Reproduction and audit

The runner loads the exact candidate test fixture from PR #7805 at the pinned head; it uses the repository's fake display and fake owner. See `RUN.txt` for the exact executed commands and worktree. The independent `audit.py` reads the retained A03 raw result and recomputes identity, ordering, release-bracket, and neutral-state checks without importing the candidate. It also verifies the pinned source blobs against `SOURCE_LOCK.json`.

This evidence is an additional construction boundary check for PR #7805. It does not satisfy Issue #59's separately gated live-control allocation.
