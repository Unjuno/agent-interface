# Native scorer sink backpressure — Issue #59

One finite native Windows construction, worker01a0ff33-df63, FINAL-v5,
claim5965233761. This archive contains the exact source/input/freeze, first20
child outcomes and actual stdout/stderr streams. It changes no production,
default, workflow, historical source or allocation. Source copies/helpers are
inert .py.txt files; the explicit raw-only verifier never invokes the producer.

The question is whether a standard same-thread bounded nonblocking byte spool
can serve a ready FINISH while retaining a scorer row under actual native pipe
backpressure. Compare exact main403a21a6951662401925835fbc70670bab84b457
with #6913 head8f5872874760b671b558a7febe4e14a23261d753, both actual adapters,
empty/full output pipes, direct/spool sinks, and four one-byte-capacity refusals.
Source command readiness/read and clock are injected; output pipes are real.
This does not test POSIX stdin select on Windows or the actual ScorerFileSink.
The named production owner's returning-callback adoption is left separate.

First run2026-10-03T03:56:57.475751–03:57:00.672518UTC produced20 rows;
first raw-only audit is PASS_PIPE_CONSTRUCTION_SCOPED with no evidence errors.
Raw SHA256 a637bf3157d00deb7c26babde7517170ea427def3cc6a2a925ee372b24e9de79;
freeze SHA2569ecfa805e979b4cb89e470386ea6793b8798e3044c31c4e6dcf29625c6a8eb68.
All20 children/readers terminate; all13 original frozen files remain unchanged.
Twenty stdout/stderr pairs bind exactly to raw and16 nonoverflow source cases
eventually process FINISH/persist the one exact sample. Native full pipes held
4096 prefill bytes in this run; that size is not assumed for other systems.

During the declared pre-drain observation window,12 conditions process FINISH:
empty direct/spool and full spool. Four full direct sinks do not show a command
until parent drain. Four capacity-one spool cases explicitly refuse without
inventing command service or a persisted row. On full spool cases the source
has terminated with a pending row; final persistence happens only after drain.
Command service and durable evidence are different endpoints. A missing command
in the200ms window is an observed censor, not an empirical infinite-hang proof.

Eight actual copied-raw corruptions are refused, including bool/int/float aliases,
consistent rehashed payload substitution, output loss, prefix and inventory loss.
The original supplemental verify_controls.py helper used assert to qualify its
aggregate under -O; its first outputs/source are retained as checks-01, and that
optimized qualification is insufficient. Versioned verify_controls_v2 uses
explicit guards and records all8 actual refusals normally and with -O in
checks-v2. Frozen producer/auditor/raw and the first disposition are unchanged;
no child deck was repeated. This archive's explicit verifier also uses guards
that remain active with optimization.

Run: python -B verify.py (or python -B -O verify.py). This verifies complete
archive hashes, frozen-file/source mappings, all first raw/native streams and
the8 stored mutation witnesses. Review/query records and future apply decisions
remain outside this source tree. Publication projections replace only4 initial
and2 v2 receipt argv spellings containing private executable/root paths; exact
private originals remain retained and their hashes/mappings are public.

Construction scope:Windows x64 CPython3.12.14/stdlib, i7-12700H, one sequential
child, one owner thread, source clock0, one initially due sample at1Hz, inert
ProgressSample. Caps are2s sink-entry observation,200ms pre-drain window,5s
completion after drain,45s outer,1MiB per output stream and4096-byte/1-byte spool.
These are diagnostic limits, not measured latency or causal speed benefits.
No game/model/GUI/input, physical release, useful feedback, controller access
to scorer payload, live/formal allocation, GPU/container/WSLc or #57/#59 closure.

Decision:keep as bounded construction evidence for sink/I/O integration. Do not
adopt this custom sink as ScorerFileSink, claim nonreturning-callback preemption,
or remove #6913's limits. Finite capacity and completion/persistence barriers
remain requirements before any relevant live application. Correct task effects
and model latency are unmeasured. This is research evidence, not product progress.

Existing mechanism/API source:[Python3.12 os.set_blocking documentation](https://docs.python.org/3.12/library/os.html#os.set_blocking).
