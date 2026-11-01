# Concurrent cancellation transaction identity

The previous owned-session cancellation released its control-channel lock
before retirement and cleanup finished. A deterministic two-thread test paused
the first cancellation in cleanup and allowed a second cancellation to run;
the first then observed the second operation's identifier. This could associate
the prestarted cleanup request with the wrong operation and deadline.

The candidate serializes the whole `cancel_guarded` transaction using a
separate per-owner lock. A subsequent request that cannot acquire it before its
own deadline returns `cancel_unconfirmed`, sends no cancellation signal,
requires review, and disallows replay. It cannot overwrite the active operation
identity while the first transaction is in cleanup. The signal's
`input_dispatched=false` does not describe the original guarded action.

In one WSLc private-Xvfb trial, an actual guarded owner pressed `a` on a
separate target and paused. The harness delayed the first cancellation just
before cleanup, requested a second cancellation, then resumed the first. The
second returned `cancel_transaction_deadline` without dispatch; the first
cleanup retained the first identity, observed owner disconnection and verified
an `a` release readback. The target also observed `a` release. The old task
and cleanup remained UNKNOWN, and a fresh guarded task succeeded. The injected
delay makes this a controlled race experiment, not a natural-failure rate.

The new deterministic test failed on the prior candidate and passed after the
change. An initial 75-test normal run had one terminal-receipt timeout; that
test passed when rerun alone, and a subsequent complete 75-test suite passed
in both normal and Python `-O` modes. The cause of the initial timeout is not
established. All those outputs, source manifests, conditions and live receipts
are retained in `raw.zip`; the conditions' `draft_head` is an older ancestor,
while the manifests identify the tested source. One test authority cookie was
checked in raw and hexadecimal form against the packaged material; authority
files and private launcher commands are excluded. WSLc reported no swap-limit
enforcement.

This serializes cancellations with each other; concurrent close and other
operations still need custody analysis. Lock and poll waits are bounded but
pipe operations, process shutdown and scheduling are not proven to meet a hard
end-to-end deadline. This draft does not establish production display ownership,
queue drainage, MAP01 completion or general release confirmation.
