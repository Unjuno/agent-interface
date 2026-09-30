# Real X11 synchronous-grab recovery discriminator

Engineering follow-up to the intermittent button-release readback observed during
#5607 and recorded on #2437. WSL3.0.1 / Ubuntu / private Xvfb+Openbox, production
base1543fb4ee6b8773bcf39230c03094f37bc691e59. No frozen allocation was repeated.
This is model-independent native input evidence, not primary visual task success.

First stage: one private server,20 fresh Tk fixtures with the same actual production
program and injected exception immediately after its left-button press. All20
release receipts were verified; separate-X-connection samples at0/2/10/50ms were
neutral. One additional withheld-release control stayed down for all four samples,
blocked ordinary input, then recovered through an explicit cleanup call. Reading
samples emitted no input. The intermittent historical failure was not reproduced.

Second stage: a new private server, three declared cases: ordinary release,
real synchronous passive pointer grab, and withheld release. The independent
connection installed a GrabModeSync button1 grab on the fixture window. The native
press activated it; the observer received ButtonPress for that window. Production
cleanup sent its release but reported left down/unverified, and all four independent
samples still observed left down. When the independent owner called AsyncPointer
and removed its grab, the queued release completed: the mask became0 with zero
additional backend input emissions. The session still required recovery. Explicit
recover_input subsequently verified neutral and returned task_success:null and
replay_allowed:false. The withheld control remained held until explicit cleanup.

This proves a real input-processing condition can separate release request from
observed neutrality. It does not prove that Openbox grabs caused #3505 or #5607's
spontaneous failures. The second-stage raw summary uses normal_count=2 to mean
both non-withheld cases, including the grab; they are not two ordinary controls.
The original summary and all raw rows are preserved without relabeling.
[Xlib's grab/event documentation](https://www.x.org/releases/X11R7.5/doc/libX11/libX11.html)
and [XTEST's request documentation](https://www.x.org/releases/X11R7.5/doc/Xext/xtestlib.html)
provide protocol context; neither substitutes for the observed trace.

Integration: one permanent real-X11 regression checks synchronized request versus
state under a passive synchronous grab, independent neutral read after allowing
queued input, persistent ordinary-input refusal, and explicit no-replay recovery.
A bounded read-only polling loop exists only in that test, not production. The
public failed-recovery note now says the input block persists and forbids a new
program/replay. The host guide explains explicit recovery, new binding revision,
and fresh observation, retaining unknown previous effects and no new lease.
No implicit retry, grab takeover, sensor, cleanup success inference or production
wait change was added.

Validation:55 private GUI/input/artifact/CLI tests and66 public MCP session/server/
guarded tests passed. Their full logs,24 native rows, programs, independent samples,
passive event logs, actual app/server exits and final source snapshots are retained
as166 files in evidence.zip. Empty cleanup state is checked separately from exits;
termination exit codes are not relabeled as normal success. No CPU/GPU, token,
useful-feedback, human baseline, isolated latency or speedup result is claimed.

Run `python -O runtime/results/x11-grab-recovery-01/verify.py` to check exact archived
bytes and selected trace invariants. This verifier performs no GUI replay or
independent adoption audit. Historical release failures and the wider #2437
failure-boundary study remain unresolved.
