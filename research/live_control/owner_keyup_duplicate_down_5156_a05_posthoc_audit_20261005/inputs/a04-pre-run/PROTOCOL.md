# Repeated DOWN while a key is held — A04

## H / T / D / C / U

**H.** The frozen A03 owner candidate accepts a second same-lease `down` for a key that is already held, emits another `input_admission` with a new owner-local ID, and overwrites the held-key-to-admission map. One subsequent `up` can produce one owner KeyRelease receipt, so the backend should classify the inventory as ambiguous and leave at least one admission without a unique release outcome.

**T.** Run one fixed fake-Xlib trace through the A03 owner v12 / transition wrapper v5 / retained backend v5 candidate: `A down, A down, A up`. A raw-only auditor independently reconstructs owner IDs/sequences, admission and release cardinalities, per-key receipt identity, caller/owner timestamp nesting, exact XTest/XSync operations, verified neutral cleanup, and six corruption controls. The formal result is scoped to this accepted direct-owner operation sequence; it does not claim the upstream application normally emits duplicate downs.

**D.** `FAIL_DUPLICATE_DOWN_RELEASE_IDENTITY_AMBIGUOUS` is the predicted scientific outcome if two distinct admissions are emitted and the one release is `ambiguous_multiple_admissions` (or otherwise lacks one-to-one release identity). A PASS would require the second down to be rejected before another KeyPress/admission, or an explicit, audited idempotent/coalesced contract that leaves no admitted identity orphaned. Candidate and auditor must each exit 0; the auditor must report zero base reconstruction errors and reject all 6/6 corruption controls. Runner/audit/provenance errors are STOP, not a scientific finding.

**C.** The fake Xlib keymap records key state, not real server event delivery. Duplicate `KeyPress` while a key is held may be illegal or unreachable through a higher-level caller; that caller-contract question is untested. This experiment exercises the accepted `InputOwner.call("down")` operation and composed backend path only.

**U.** This diagnoses only duplicate same-key DOWN identity accounting in the research candidate. It provides no real X11, physical release, client event, game, feedback, recovery, latency, task-effect, safety, or authority evidence. No #59 live allocation is used or implied.

## Frozen lineage and envelope

The baseline is current `origin/main` `a9352dc53c783f1501046d762bc36c34bc6ab480`; all seven copied owner/wrapper/backend/fake-Xlib dependencies are byte-identical to the A03 package pinned to that main. Candidate logic is unchanged from A03; only the trace and scientific discriminator differ. Allocation identity: `OWNER-KEYUP-DUPLICATE-DOWN-5156-A04-20261005-01`.

Use cached WSLc `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`, image ID `sha256:414a398990af718f018ff9c23cea0e7489b7986eb54f2b1d7cc874c99ebc7364`, linux/amd64, Python 3.12.15. Candidate and auditor each run once in separate disposable containers, one CPU, network disabled, read-only source and separate writable output. No pull, memory cap, or retry. The host cgroup/swap limit is unverified. The separately gated #59 live lane is not involved.
