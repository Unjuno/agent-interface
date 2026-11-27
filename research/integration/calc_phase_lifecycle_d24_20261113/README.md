# D24: one compiled Calc phase through the current host and WSLc

One new, non-retried qualification run on 2026-11-13 JST completed a compiled
Calc entry-and-save phase. It entered A1=538 and A2=726 in the isolated Calc
application. A separate XML parser checked the retained saved document for
exactly those two numeric cells. Explicit owner-close release and independent
X key/button readback were neutral. Host and container exited 0; a subsequent
check found the named container absent and the recorded host PID absent.

This supports one-phase integration qualification only. It is not warm reuse,
an invalidation/repair result, a matched speed comparison, or completion of #57.
Formatting collateral and arbitrary descendant lifetimes were not separately
scored. The outer launch record deliberately keeps task_success unknown; the
independent task and release audit is a separate result.

## Conditions and observations

- Runtime base: `1bd8a3998fc6f1595b21455dc5fce3c10d76ff8d`.
- Prepared private source derived from the reverse Calc three-arm archive,
  with phase-qualified exchange, explicit values and per-phase baseline hash.
  Historical expected-value pixel comparison was replaced by parameterized OCR.
  Known task values and the scripted Save remain controller assistance.
- WSLc Linux image: `sha256:6150a4f3c779a51b3ac6a7d93bc1d0450803325efb7ab38ade8b1aaf79c33e25`.
  Network none, CPU 1, memory 1 GiB requested, pull never. Swap limiting was
  unsupported; no total RAM-plus-swap cap is claimed.
- Current Windows Codex CLI: `0.167.0-alpha.4.1`; Python host 3.14.2.
- One `gpt-6.1-sol`, low-effort screenshot-grounding call; input 12,201 tokens,
  cached input 0, output 78, reasoning output 0, cache write 0.
- Graph receipt: TASK_SUCCEEDED / method_complete. No extra recovery Save or
  entry replay. Phase returned with owner open; outer finally then closed it.
- Task interval 6.621614243 s; outer invocation 12.0605017 s. These nested
  intervals are not additive. Outer duration starts after this packet's source
  preparation; it is NOT full lifecycle economics. No speedup is inferred.

## Evidence and limitations

Original private packet: `calc_phase_lifecycle_20261113_d24`. It retains frozen
conditions, source, exchanged screenshot/request/response, provider protocol,
operation/capture receipts, saved FODS, cleanup, independent audit and 211-file
result manifest. Manifest SHA256:
`804cd66486f179b57a1d311f406259d49fdae9edb4e1dc72d932cea57ece6aa7`.
All frozen input and result manifest entries were read back without mismatch.
Saved document SHA256:
`28bd52c34639ae7af637cca55b879b930b32879364e501dfb929cb13fcb3997b`.
Raw remains on the authorized local host, not recoverable from this report or
its hashes alone. Provider/session details are not republished here.

Preparation tests covered stage mismatch refusal before provider invocation,
distinct stage accounting, already-satisfied-task refusal before input, and
cleanup continuation after Docker inspection timeout. Normal and optimized
tests passed for these focused paths. An earlier Windows saved-file identity
test failed once and then passed; its cause remains unresolved. It is retained
in D18 and is not overwritten by this Linux run.

Next: retain the same owner across distinct tasks, establish genuine reuse of
the intended compiled plan, and test dependency invalidation plus one bounded
repair. Per-phase construction must not be labelled warm compiled reuse.
The fixed three-arm comparison must include failed/preflight attempts, model
accounting and preparation/cleanup boundaries before any efficiency claim.

This publication changes no runtime, experiment launcher or test discovery.
