# Issue #3947 — regular-file admission, allocation c82e-01

Allocation `input-kind-c82e-20260922-01`; initial main
`b2457b746a6df06f6536585dfe2ab937aff639f4`.
Upstream reader Git object `ea72c166c2cea511ea91031dfbb14563fe4e3245` is copied
byte-for-byte into `upstream/reader.py` (3,689 bytes). No upstream runtime change.

## H / T / D / C / U

H: an input byte bound does not bound the blocking open/read of a FIFO. Opening
once with O_NONBLOCK, checking fstat for a regular file, reading at most 513 bytes,
and giving the exact reader a private snapshot should refuse non-regular inputs
without changing regular-file notification/cursor semantics. This is input
admission research, not a claim that the original append-only JSONL reader
promised to support FIFOs or satisfy a hard real-time deadline.

T: two policies EXACT_READER / REGULAR_SNAPSHOT_ADAPTER; seven input cases
COMPLETE, INCOMPLETE, OVERFLOW, SYMLINK-to-regular, DIRECTORY, FIFO_NO_WRITER,
FIFO_LIVE_WRITER. Three repetitions of all cells, alternating arm order by
(repetition + case index) parity: 42 first-outcome rows. Three fixed JSONL
notification records; max_bytes=512 and max_records=32. INCOMPLETE removes only
the last LF; OVERFLOW adds 600 spaces to the complete input. Fixed caller-owned
stream lifetime `issue3947-fixed-lifetime`; no cursor persistence or restart.

Each reader is a fresh exec'd Python process. A ready/GO pipe barrier excludes
interpreter startup from the external 1,000,000,000 ns response deadline. The
supervisor records exact ready/response bytes, clocks, source hashes, process
exits, input bytes and stat identities. TIMEOUT means no response by that deadline
and process observed alive. Only the owned child is terminated with SIGTERM and
reaped; a different exit or missing evidence fails audit. It is not an assertion
of permanent deadlock. No retries, replacement rows or threshold changes.

FIFO_LIVE_WRITER construction: a temporary Linux RDWR nonblocking anchor lets a
separate exec'd writer open O_WRONLY and report ready. The supervisor closes the
anchor BEFORE reader GO. The writer remains alive with its write descriptor open,
emits no FIFO bytes, waits on its control stdin, then closes normally. Neither a
new sensor nor a background event producer is implemented. The anchor is not
present during the measurement. Writer PID/inode/mode/readiness/close evidence is
retained; zero data writes follows from the frozen source and protocol, not an
independent syscall trace.

D: source/process/input identities and all 42 ordered cases must reconcile.
EXACT_READER: all six FIFO rows TIMEOUT, all nine regular receipt rows match exact
bytes/cursors/tail states, three overflow rejections, three directory errors.
ADAPTER: nine non-regular refusals, nine exact regular receipts, three overflow
rejections, no timeout. Every exposed receipt has authority=none, acknowledged=false,
input_dispatched=false. Both FIFO types must be exercised with owned-process
cleanup complete. Raw-only independent auditor must have zero errors and reject
eight corruption challenges. A complete behavior disagreement is scientific FAIL;
source/setup/control timeout/cleanup/evidence ambiguity is STOP/HOLD. Unsafe
input handling does not become safe because the boundary hypothesis passes.

C: supplied Linux x86_64 execution container, Python 3.13.5, stdlib only. Docker
CLI absent: NOT Docker Desktop/OrbStack replication. No installation, provider,
model, GUI/input, network experiment, action, ACK, production CLI or shared code
change. Symlinks to regular files are deliberately allowed, validated after a
single open. O_NONBLOCK is not a universal deadline for storage/device operations.

U: no remote/slow filesystem, power loss, hostile file/device, in-place mutation,
arbitrary path-replacement, filesystem reclamation, producer epoch, multi-reader
commit, crash persistence, model viewing, useful-feedback timing, task success or
production promotion claim. Adapter makes an additional bounded copy and temporary
file; no latency/throughput benefit is claimed. Audit is independently implemented
and separately executed, but authored by the same agent, not an external review.

## Collision and roadmap

#493 already had its exact formal study; #2547/#3934 is owned elsewhere. Preserve
closed #462, #3883, #3917 and all historical data. Parallel #3931 covers host crash
persistence; #3933/#3937/#3938 cover epochs/rotation; #3941 covers concurrent cursor
commits. This study does none of those. Reader+FIFO search found no matching
allocation before #3947; the branch collection/Issue searches are bounded, not
claims about unpushed/private work.

Owned path `research/integration/passive_reader_input_kind_c82e_v1/`; branch
`research/passive-reader-input-kind-c82e-v1`. Bounded roadmap: exact source recovery
-> excluded construction -> public freeze -> one 42-case experiment -> raw-only
audit/corruptions -> report/PR -> main verification -> cleanup only if safe.
The overall ROADMAP and #3876 remain open. No other branch is eligible for deletion
merely from age, ancestry, an absent result file, or a perceived lack of activity.

## Construction history (excluded)

construction-01 ran 14 rows (one repetition) with unchanged final experiment,
audit and test sources. Driver RAW reports COMPLETE. The encompassing tool call
had a 20-second timeout; the retained driver wall interval was 27.782796835 s and
its complete raw/stdout were subsequently observed. No first test command exit
was retained, so that wrapper is not claimed successful. An explicit separate
construction-tests-02 invocation exited 0: 9/9 tests, baseline plus eight
corruptions. No formal execution occurred during construction. Raw first outcomes,
empty original test logs and wrapper-timeout disposition remain retained.

## Reproduction and source gate

`python -B launch.py` checks every FREEZE.json digest, writes an exclusive
FORMAL_INVOCATION.json and execs the runner once into fresh formal-01. Once either
output exists, do not delete it or invoke a replacement allocation under this ID.
A future rerun requires a new Issue/allocation/path/freeze; it is not a retry of
this result. Run the retained-result audit independently with:

    python -B audit.py formal-01/RAW.json FREEZE.json

Construction corruption tests only (not another experiment):

    python -B test_audit.py construction-01/RAW.json

Primary background references (not empirical outcomes):
- POSIX open: https://pubs.opengroup.org/onlinepubs/9799919799/functions/open.html
- POSIX read: https://pubs.opengroup.org/onlinepubs/009604599/functions/read.html
- Python OS descriptors: https://docs.python.org/3/library/os.html

The raw-only auditor does not import the experimental reader/adapter/runner.
