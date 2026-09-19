# Text payload preflight v1 — finite plan

Task: TEXT-PAYLOAD-PREFLIGHT-V1-20260916-01.
BASE: 29a9c45c87cf59d6d9116b157eed6e737b1311f3.
New namespace only: research/text_payload_preflight_v1/**.
Read-only baseline: research/runtime_backend_x11_v0/backend_x11.py, Git blob b4f8e043ce4f8929d446e038418ea0fd3655bab0 (hash enforced by runner).
Motivation: PR #226 / source 3bc985e268aad22130a1476a30653858cac3d98f assigns direct_keys ASCII coverage, but actual retained backend validates only each next character and uses symbolic-key mapping without complete printable coverage. This is a scope mismatch, not a new token claim.

## Hypothesis and candidate

H: complete payload planning before commit prevents deterministic invalid-suffix partial writes; a live first-group/level-0-or-1 keymap plan supplies explicit Shift for printable ASCII without clipboard or global-map mutation.
The candidate's supported domain is U+0020 through U+007E, length 0..16384, and only symbols present in first-group levels 0/1 of the current map. It rejects controls, non-ASCII, malformed contexts, missing mapping and nonneutral input; checks observation, binding, expiry, focus and map before commit. Current observation/revision are caller snapshots, NOT newly measured freshness. Midflight focus/deadline interruption is partial, not atomic rollback. X server synchronization, asynchronous layout/modifier changes and hard process death remain limitations.

## Frozen finite evaluation

T1: 13 deterministic unit tests (including exhaustive 128-code-point checks on a synthetic limited map).
T2: real separate-process Tk receiver on authenticated disposable Xvfb 1024x768x24 + Openbox. Payload = 'office' + one code point 0..127 + 'tail'. Both baseline and prepared method once per code point; even code points baseline first, odd prepared first. 256 comparison trials. Four additional prepared-only controls: stale observation, stale binding, expired lease, wrong target. Total 260 trials; 132 prepared trials. Receiver reset/scoring IPC is harness-only, not an agent API. Every input event and actual receiver text retained.
T3: real LibreOffice Writer native ODT. Frozen payload order: 'office_tail', 'office\ntail', 'office!tail'; baseline then prepared for each. Six fresh Xvfb/Openbox/Writer/profile/document sessions. Initial paragraph 'sentinel '. Save is a separate harness operation after the text receipt. A separate Python process reopens ODT, checks ZIP CRC and exact paragraph text. Executor never reads output document while acting.
Constant requested pacing is 12 ms after each character for both methods. Extra candidate checks differ; elapsed time is diagnostic only, not a performance comparison. No model/provider calls.

D: Prepared passes only if every supported payload is exact with no error, every unsupported or invalid-context request is rejected with zero text emissions and no receiver text/events, all checks preserve keymap hash/clipboard owner/text, and physical keys and button/modifier mask end empty. Writer applies the same rule to durable paragraphs. Baseline failures remain published. Abstention is NOT successful text delivery. A run/harness exception is retained as FAIL/UNCERTAIN, never silently retried. Each named result directory is created exclusively; no replacement runs. GUI and Writer are separately named one-shot result allocations from the same frozen sources.

C: correct release does not imply no partial semantic effect; generic ASCII labels can overstate concrete backend coverage. XKB groups, IME, alternate apps and focus races may defeat simple two-level lowering. Type/schema checking is not model-grounding verification.
U: single private host, default map, synthetic Tk receiver + three bounded Writer payloads. No Unicode/IME, clipboard-free Unicode, real desktop, Wayland/Windows/macOS, token saving, general Office reliability or atomic commit claim. This is an integration candidate, not a shared ABI edit.
