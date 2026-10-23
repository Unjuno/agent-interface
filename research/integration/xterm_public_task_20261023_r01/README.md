# Real xterm public-MCP saved-effect task — R01

**PASS_SAVED_XTERM_EFFECT_SCOPED.** One newly frozen native WSL2/private authenticated Xvfb trial used the current public guarded MCP caller to type `record a1` plus Return into a real pinned Ubuntu xterm/interactive `/bin/sh`. The frozen task command appended exactly one journal row with argument `a1`, both stdin/stdout attached to a terminal PTY, and ancestry matching owned xterm PID371. Its fsync-completion receipt and an independent file read establish the saved effect separately from tool return. No model call or input retry was used.

This moves beyond a synthetic X property: actual xterm keyboard translation and a real interactive shell must execute a separate process that performs a non-idempotent filesystem append. The record command is still a custom fixture behind that real application. The task is known and the controller does not infer command semantics or plan with a model. Directly invoking the helper could produce the same saved artifact without any GUI; this result does not establish superiority over that simpler route, general terminal automation, a second Calc/MAP01 task, or matched efficiency.

## Effect timing and oracle

- Public input invocation→return:65.438445ms.
- Input invocation→helper fsync completion:72.875542ms.
- In this sample the saved effect commits7.437097ms **after** the public input has returned `completed`. Tool completion is therefore not used as the task oracle.
- Only after the authored input, the controller performs bounded command-free reads (2s bound, then250ms duplicate observation). Exactly one line is present; helper PID374 has shell parent372 and xterm ancestor371. The raw original journal, separate done receipt and public/native messages are retained.

Intervals are shared-kernel monotonic nanosecond differences converted to milliseconds. This is one sample without an injected fault, comparison arm or error estimate. The250ms duplicate horizon is finite; it does not prove arbitrary future exactly-once semantics. The helper records fsync completion, not pixels/model acknowledgement or an arbitrary application transaction.

The [independent saved-file auditor](audit.py), frozen before execution, passes [14 checks](audit.json): literal one-row/argument, actual PTY, owned terminal ancestry, commit ordering, public input/close, original request count, neutral keymaps, source generation evidence, owned cleanup and zero model calls. It does not import the runtime task scorer. `task_success` is an external test verdict, not a new input-authority or runtime completion guarantee. Native PNGs show the real terminal prompt; no post-task screenshot is claimed.

## Frozen conditions and environment

Base main `338973df3d9eb19b00ca42fdee935a5b058002fc`; source/helper/auditor freeze `36320756a`; conditions freeze `161d3387e` before attempt entry. [conditions.json](conditions.json), [221 source identities](SOURCES.json), [53 native binary/library hashes](native-binaries.json), all Python dependency versions and actual host command/exit are retained. [Rootless setup](../xterm_local_setup_20261023_r01/README.md) pins official Ubuntu package bytes; no package is installed during the formal trial.

One owned authenticated Xvfb `:188`, TCP disabled; rootless xterm390 with `-ut` (no utmp recording), private HOME/ENV/PATH/cache and custom task command, two inherited CPUs/nice+10. Mapped-title readiness is bounded5s followed by fixed1s settling; one known static prompt texture is explicitly observed/minted before input. The public path is same-process `guarded-x11` with process identity enabled. It does not exercise the prestarted cancellation supervisor or a real provider/model route.

The system package database and ordinary desktop are unchanged. This is native WSL2 on the user-selected PC, not a WSLc or Docker allocation. Host fonts/OS remain host-specific despite binary hashes; no universal portability assertion follows.

## Cleanup and remaining boundaries

The public owner closes normally and the independent final32-byte keymap is all zero. Owned xterm is deliberately terminated through its retained pidfd and returns exit15; that is a cleanup outcome, not a natural application exit0. Xvfb CONT/TERM/reap returns0. Separate [cleanup readback](cleanup-recheck.json) finds server367, xterm371, shell372 and command374 absent, with no remaining display lock/pathname socket. The private Xauthority and temporary HOME are removed; setup bundle persists for future separately frozen work. Complete logs/warnings are retained.

No prior trial was replayed or old raw/result edited. This qualifies one current public-caller saved task on an actual terminal application. Stalled-I/O task/recovery transfer to this app, dynamic target changes, physical/MAP01 control, provider integration, matched calls/tokens/latency/resources and repeated reliability remain open. The full goal is not complete.
