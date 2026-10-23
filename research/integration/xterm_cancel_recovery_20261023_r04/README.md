# Real xterm cancellation and new-generation recovery — R04

## Frozen question

Can the standard guarded MCP caller retain an old task as `UNKNOWN` when a real xterm input is blocked at the existing delayed-XTEST / real `Display.sync()` fault boundary, then complete a different saved task on a newly observed xterm process and window generation after the old request's finite delay horizon?

The old command is `record old04`; the new command is `record new05`. They write to separate fsynced journals. The experiment records the old journal at cancellation and again after the nine-second horizon. Either zero or one old effect is retained as an observation; the old runtime result must remain `UNKNOWN`, with task success unset and replay disallowed. The new attempt must produce exactly one `new05` record, retain its fsync receipt, use a distinct process/window generation, and have an independent all-up read before the new target receives focus.

## Fixed setup

`conditions.json` fixes the native WSL2 private Xvfb `:188`, rootless Ubuntu xterm390 bundle, 8,000ms delayed request, 9,000ms horizon and 3,000ms cancel response bound. No container allocation, package install, model call, native Windows desktop input or retry is part of this run. `native-binaries.json`, `ldd-xterm.txt` and `pip-freeze.txt` retain the observed executable, resolved library and Python environment identities. `SOURCES.json` binds the trial, task helper, independent auditor and runtime paths to the pre-run source.

The task helper is installed only into each private xterm's temporary `PATH` and runs only after the typed shell command. Its append journal and fsync-completion receipt are the task oracle. The trial calls the public MCP server in-process and retains the public/native records. The old request is issued exactly once; cancellation does not clear its unknown result. After the finite late-request horizon and an independent neutral keymap read, the old xterm session is retired before a new xterm is focused.

Before freezing the formal trial, an input-free app preflight is retained. Its first setup attempt failed because the xterm inherited `DISPLAY=:188` while its private server was `:189`; the error log and cleanup recheck are preserved. A second setup used private display `:190` and passed: real `XTerm` window, interactive shell on `/dev/pts/2`, zero keymap, no journal effect, xterm session exit15, Xvfb exit0 and empty process groups. Its report hash is fixed in `conditions.json` and checked again by the formal runner.

## Decision rule

`audit.py` independently reads retained files and native process records without importing a runtime scorer. A scoped pass requires: the injected sync fault is reached; cancellation returns within the frozen limit; old terminal status preserves conservative `UNKNOWN`; old application effect count is zero or one and is not relabelled; delayed horizon and all-up read precede new focus; old process session is absent; the public caller observes distinct target generations; the new PTY task creates exactly one independently read `new02` effect; and new application/session cleanup succeeds.

Any failed assertion, timeout, source mismatch, cleanup residue, unexpected old effect multiplicity, wrong generation, or oracle mismatch remains a retained failure. No trial is retried. A pass is one xterm sample using a custom task helper and a preexisting XTest fault injection. It does not prove arbitrary application transactions, natural terminal exit, real provider/model behavior, Windows desktop control, MAP01, broad reliability, or matched efficiency.

R03 reached the delayed-request and sync boundary but failed before cancel because its runner watched the wrong marker directory. The corrected R04 runner reads markers directly from the public output root and counts input requests at that same root.
