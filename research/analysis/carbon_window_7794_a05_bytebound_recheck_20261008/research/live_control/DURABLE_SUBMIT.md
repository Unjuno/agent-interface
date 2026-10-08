# Durable submit journal across caller process loss

`durable_submit_v1.py` is a Linux-only candidate that wraps submit and command-free reads. Before any transport callback, it saves the exact request and generated request/action identities with `may_have_been_sent`. Temporary-file fsync, atomic replacement and directory fsync precede transport. A kernel flock serializes cooperating processes throughout the bounded exchange and commit. Failure or process death leaves the pending record; the next process refuses all new submissions before invoking transport.

Reconciliation requires the exact command echo, matching admission and matching terminal with verified release and empty held-key/button sets. Admission alone is insufficient. Another command echo makes attribution uncertain and retains the lock. Resolution is historical execution evidence, never task success or renewed input authority. The caller still needs a fresh observation and valid admission deadline for each later action.

## Measured scope

`probe_durable_submit_v1.py`, results/durable-submit-01: five separate worker invocations. The first exits17 inside the injected transport callback, after the pre-send journal commit and before real network activity. Two later submit attempts are refused without invoking their transport callbacks, including one after admission has been recovered. Separate read workers consume an admission slice followed by the terminal slice; the event cursor moves17 to19 to47 and the pending identity survives the process boundaries. Four controls retain uncertainty: terminal without echo, echo without admission, intervening foreign command, and terminal reporting a held button. A competing subprocess fails with BlockingIOError while the journal lock is held. Source hashes are pinned before the run.

Recovery responses derive from the previously recorded actual Inkscape lost-response trace, with command and action identities rebound for this fixture. These are injected replies, not a new live GUI or socket experiment. The resumed observation remains historical. This does not measure model speed or human parity.

## Boundaries and next experiment

Linux flock/fsync ran under WSL on the mounted Windows repository filesystem. This verifies ordinary process loss and cooperating-process exclusion; it does not prove power-loss durability, storage fault behavior, hostile checkpoint integrity or cross-filesystem guarantees. Initialization is only for a caller-owned session without an already unresolved command; the journal cannot police another client bypassing this API or creation of another journal. It has no reset/retry escape hatch. An uncertain pre-send crash can therefore stay unresolved indefinitely if the server never received the request.

Only submit/read are exposed. Cancellation, clock and finish are not integrated yet. The existing runtime rejected event lacks an action/request identity; v1 conservatively retains uncertainty after rejection instead of guessing attribution. Event gaps, malformed replies, channel closure and transport failures also cannot prove runtime termination. This is not a default caller replacement or a complete session supervisor.

Next bind the journal to one real long-running session, crash the caller after an actual write, resume with a new caller process, and verify that recovery is read-only while the same runtime is live. Also make rejected outcomes attributable before adding automatic rejected-resolution behavior. Keep the existing actual Inkscape result separate from this injected replay.
