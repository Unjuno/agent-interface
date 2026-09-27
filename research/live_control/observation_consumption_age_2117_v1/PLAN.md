# Capture age at the process-consumer boundary — Issue #3953

Parent #2117 remains open; closed #361 and all historical results remain unchanged.
BASE: b2457b746a6df06f6536585dfe2ab937aff639f4.
Owned branch: research/observation-consumption-age-2117-20260922.
Owned path: research/live_control/observation_consumption_age_2117_v1/**.
Allocation: observation-consumption-age-20260922-01.

## H / T / D / C / U

H: arrival-restamping falsely admits old process-delivered pixels. Preserving the
native acquisition interval rejects delayed packets without confusing delivery
with capture. This is an age/identity receipt boundary, not input authority.

T: one fixed sequence of prompt, delayed_same, delayed_changed, missing, boolean,
reversed, future and stale_identity; repeat exactly three times (24 first rows).
Both policies evaluate the identical packet at the same consumer timestamp.
AGE=100000000 ns; delayed publication waits at least 150000000 ns after the native
acquisition end. Source age uses acquisition START as the conservative age bound.
The private Xvfb root ROI changes only in delayed_changed, after acquisition and
before publication. All packets retain full losslessly encoded 32x32 BGRX bytes.
The consumer has no access to the independent current-pixel oracle.

D: PASS_CAPTURE_AGE_BOUNDARY_SCOPED requires all24 source/clock/pixel/protocol/exit
checks, both prompt admissions, candidate rejection of every delayed/malformed/
stale-identity case, changed-screen disagreement for all three changed cases,
unsafe comparator admission of the delayed frames, neutral input and independent
audit plus 12 rejecting corruption controls. A late positive is HOLD rather than
resampled. A source/transport/oracle/cleanup failure is STOP and retains partials.
No formal rerun, replacement, gate tuning or extending the schedule is permitted.

C: the two policies share exact pixels, transport and consumer time. Therefore the
contrast is timestamp semantics, not an acquisition implementation speedup. The
150 ms barrier constructs an ordering counterexample, not a natural latency
sample. Arrival-restamping is a deliberately unsafe comparator; no allegation
is made about the production runtime. Even a timely image may be semantically
stale within its age budget. No actions are authorized by this experiment.

U: no model acknowledgement/calls/tokens, task-effect score, held-out application,
GIL attribution, natural backlog probability, Docker/OrbStack replication,
physical scanout, hard-real-time guarantee, production promotion or speedup.
Monotonic clocks are compared within this same execution container; the
/proc/self/ns/time entry is unavailable. No child changes namespaces. Parent
send/receive and native/Python enclosures are checked per case; this is not
cross-host clock synchronization or a quantified physical-time error bound.

## Commands and roadmap

1. Restore the inherited native.c verbatim: Git blob
   92b2ca11117f6bcb80f45dbac62e16d62bb4f6fd, 2289 bytes.
2. Build: gcc -O2 -Wall -Wextra -Werror -fPIC -shared native.c -o native.so -lX11.
3. Run synthetic units: python -B -m unittest -v test_study.
4. Excluded construction: python -B study.py --construction --out UNIQUE-SCRATCH.
5. Freeze sources, exact native binary, environment and this plan before formal.
6. Exactly once: python -B study.py --out formal-01.
7. Read-only audit: python -B audit.py formal-01/raw.jsonl --freeze FREEZE.json --mutations.
8. Publish raw bytes, construction incidents, source identities and report by PR;
   read back merged main, then assess ONLY this branch for safe cleanup.

Historical allocation IDs must never be rerun. A reproduction uses a fresh ID and
separate paths. The repository-wide roadmap is not completed by this scoped rung.

## Construction record

construction-01: STOP before Xvfb/rows because /proc/self/ns/time was absent.
The exact attempted source and stderr are retained; the field now says unavailable.
construction-02: STOP before rows because inherited XAUTHORITY pointed to a missing
file. A new empty authority file scoped to our own private display fixes setup;
Xvfb listens on no TCP endpoint. No host display or authority file is modified.
construction-03: two complete rows and a partial third, then the independent
Python-Xlib oracle returned str for UTF-8-decodable pixels. Its String8 parser
was inspected: successful UTF-8 decoding is reversed with UTF-8 encoding, while
bytes pass unchanged. Original cleanup also raised, so the known owned Xvfb PID
was command-line-verified and terminated. Original wrapper exit remains 1 and
original child exit remains UNRECORDED; the rescue is not a clean original exit.
construction-04: eight complete excluded rows, independent audit PASS, all12
mutation controls rejected; synthetic unit suite 6/6 passed. These are not formal
observations. No thresholds, native source or scientific schedule were changed.

## Upstream technical references

Python 3.13 time.monotonic documentation (same clock across processes, not wall clock):
https://docs.python.org/3.13/library/time.html#time.monotonic
Xlib specification (XGetImage software acquisition semantics):
https://xorg.freedesktop.org/archive/current/doc/libX11/libX11/libX11.html
Installed Xlib.protocol.rq.String8 parser source is hashed in ENVIRONMENT.json.
Independent auditing means separate implementation/process, not another person.
