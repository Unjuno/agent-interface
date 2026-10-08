# Native sink backpressure construction — #59

Worker01a0ff33-df63-7d60-871f-a7ecd2649d07; FINAL-v5; claim5965233761.
No production change, adoption ownership, committee vote or main apply.

H: under actually full native output pipes, the existing synchronous sample/sink
call holds ready command service until output drains. A standard same-thread
nonblocking byte spool can let a ready FINISH be handled within the declared
observation window while preserving a finite row for later persistence. Capacity
exhaustion must refuse explicitly, without fabricating command or persistence.
This is an identified limitation already excluded by #6913, not a new allegation
against its claimed returning-callback scope. The new question is the bounded
standard comparator and its distinct command/persistence endpoints.

T:20 sequential children:2 pinned source arms x2 adapters x2 sink modes x2
initial output-pipe states, plus4 full-pipe one-byte-capacity negative controls.
Clock is fixed zero; one sample is initially due; input readiness/read are inert
ready FINISH. Source sample/command/sink remain on one owner thread. Output is a
real Windows anonymous pipe. Full state is constructed by nonblocking writes
until the final one-byte write refuses. Direct mode then switches to blocking;
spool mode keeps nonblocking output with4096-byte pending capacity. Source and
the exact row are retained. Only parent stderr metadata is observed before
drain:200ms after sink-entry observation (early ready-command delivery wakes
the window). Then parent starts its native stdout reader, sends DRAIN, reconciles
all bytes and terminates the owned child. Source termination precedes final
spool persistence; those are separate endpoints.

D:scoped construction PASS requires all20 fixed cases, no child timeout/reader
error, all children/readers terminal, one owner/sample, exact native prefix+row
bytes, correct command endpoints, and overflow controls explicitly refusing.
Before parent drain: empty direct/spool and full spool must deliver FINISH;
full direct and capacity-one spool must not have an observed command. After
drain: all16 nonoverflow cases must deliver FINISH and persist one exact row;
4 overflow cases retain refusal and no fictitious output frame. Literal payload
and receipt types are reconstructed independently from raw; no source import
in the auditor. Unexpected/missing evidence is FAIL/HOLD, never dropped or
relabelled. Original run/raw/first audit are immutable. Directed copied-raw
tamper controls are separate from the producer and do not spend another run.

C: nonreturning sink cannot be preempted by these synchronous source loops;
the direct result is compatible with source inspection, not surprising evidence
of a defect in #6913's limited adoption. Early command service does not prove
scorer evidence durable, game cleanup, input release or task success. A finite
spool does not provide an infinite-outage/flood guarantee. Controller handlers
only see FINISH; scorer metadata is collector-side and never their input.

U: Windows x64 CPython3.12.14/stdlib; actual output pipes, injected command I/O
and source clock, typed inert ProgressSample. Not actual ScorerFileSink, POSIX
stdin select, game/DoomGame, model, GUI/input, physical release, useful feedback,
latency comparison, general safety or R134 result. Observation windows and
process scheduling can censor a pre-drain event; retain that outcome. No formal
or consumed allocation, WSLc/container/GPU/shared runtime or new worker.

Limits:5s child completion after drain,2s sink-entry wait,45s producer outer cap,
1MiB per output stream/prefill cap, one sequential child,4096-byte spool or1-byte
negative control. OS pipe size is observed, not asserted across platforms.
No worker configuration, common deadline/N or old formal source is changed.

Standard API provenance:Python3.12 added Windows pipe support for
os.set_blocking; official https://docs.python.org/3.12/library/os.html#os.set_blocking .
Initial separate native availability check produced4096 bytes then
BlockingIOError within1MiB. That setup check is not a deck result.
