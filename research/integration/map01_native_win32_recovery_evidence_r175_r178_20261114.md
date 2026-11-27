# MAP01 native Win32 recovery evidence R175–R178 (2026-11-14)

This note indexes four distinct native Windows attempts. Their raw packets remain local-only under the originating task workspace's `private-packets/`; the records below preserve attempt identity and checksums without copying raw captures into the repository. Never combine their outcomes or replay an attempt.

## R175 — producer-only abnormal exit

Frozen conditions preregistered one native `SendInput` LEFTDOWN (accepted count 1), a 120 ms hold, then producer-only `os._exit(86)` without backend cleanup. The retained result records one dispatch, automatic bounded cancellation recovery, source action `unknown` with `release_confirmed=false`, cancellation release confirmed, a two-second integrated late-input horizon, a continued independent neutral horizon, and the exact ammo change 50→49. `task_success` remained null and replay was denied. The exception-to-supervisor verified-release interval was 16 ms against the 750 ms bound; this is not raw SendInput-call latency. One sample does not establish reliability or MAP01 completion.

- Conditions SHA-256: `84ceda5823b535e716f1144b497427978b93ae75d4c615ed5881e0446d7add34`
- Result SHA-256: `6c96e50f1d1d78ae7e8a9c4a396d1dfa206597f22b8e5d0d4f3071e6558dfc3a`
- Postrun manifest: 735 entries; all present with matching size and SHA-256. Manifest SHA-256: `0c98b3b748c7b29eacce3b5fede57561f1bb3fc4a4b9648aea7c5f8b3167fadf`
- Frozen source head: `ba85146d3c67e111881461c6d55338e8ff9e9210`; conditions record origin/main `09740752e04bbca69b512badb6879b65e98c1bdf`.

## R176 — strict harness failure R02

Classification is `PARTIAL_EVIDENCE_STRICT_PREREGISTRATION_FAIL`. The raw run contains a producer exit 0 after the observer timeout, one accepted DOWN followed by two accepted UPs (explicit UP plus `release_all`), and a post-stop independent neutral horizon and 50→49 HUD classification. The run is not a strict pass: the harness expected a bare `TimeoutError` while the public error was `UnverifiedProducerNeutralReadback`, discarded the saved pending-after-expiry row in its summary, and preregistered duplicate UP sources. Preserve this as a failed attempt; the post-stop observations do not repair its strict result.

- Frozen conditions SHA-256: `8f2484b0a28297cfbd04fac79b5483f7174e21ffd6a807fbddd92f2c79d4dd4a`
- Post-stop adjudication SHA-256: `91ff85f2946eb87aec522cedc748bfd78876e9081fd5d62a34230fc98626788b`
- The adjudication lists nine evidence files; all nine exist and match their recorded sizes and hashes.

## R177 — public result-scope assertion failure

Classification is `PARTIAL_EVIDENCE_STRICT_PREREGISTRATION_FAIL`. Its terminal evidence independently records the source action as `unknown`, source release unconfirmed, cancellation recovered with release confirmed, task success null, replay denied, two native events (one DOWN and one UP), a verified two-second neutral horizon, and the 50→49 effect. The strict failure is a caller-projection mismatch: the harness asserted that the top-level result-query envelope had `input_dispatched=true`; in fact the nested action had `true`, while the query envelope correctly had `false`. Do not relabel the raw attempt as a pass.

- Frozen conditions SHA-256: `ae9f35d905ebf1f1298704cc5f74e9c309bcc33c8fbab3f05d64a6190463d326`
- Post-stop adjudication SHA-256: `1078ef9b0cbc106adf4a5d3065281cf3c6e19da36ad53a8542df3a54c8f36eac`
- The adjudication lists nine evidence files; all nine exist and match their recorded sizes and hashes.

## R178 — scoped native observer-failure recovery pass

Classification is `PASS_SCOPED_OBSERVER_FAILURE_RECOVERY`. The frozen source was `5f97f67f83a1ac3aef07dcc7e8501f9c7f58fa3b` (tree `e1d2f246f69ddb595977281ccbd31b335e032b25`). One dispatch and one same-session recovery followed a forced normal-completion observer timeout. Recovery completed after authority expiry; the public result query preserved the source action as `unknown`, `release_confirmed=false`, `task_success=null`, and `replay_allowed=false`, while the separate cancellation record confirmed release. The run verified its late-input horizon and independent neutral horizon, observed exactly one accepted DOWN and one UP, and independently classified ammo 50→49. The observer-timeout-to-supervisor-receipt interval was 16 ms against the 750 ms bound.

This attempt's producer exited normally with code 0. It therefore strengthens the native observer-failure/result-query path but is not a second abnormal-producer-exit sample. It remains one scoped sample and does not establish reliability, MAP01 completion, or efficiency.

- Frozen conditions SHA-256: `fb205cc35fb9abf749861b1b21d26e6a81dd559dfe5b71dbf5dca8765048e152`
- Result SHA-256: `37018e22512a3d107a73e7af52bffd91a4b0d0f862c46694caf6b94759c423fb`
- Evidence manifest SHA-256: `aca1f86aae70336afe081954413ed32e4e664fb359e59385df2867949a0c124d`; its 320 files all exist and match recorded sizes and hashes.

## Integration boundary after R178

PR #10286 added a current-main public-caller regression that holds delayed recovery and observes the pending result before the recovery receipt, then observes the recovered terminal result. Its normal and optimized local runs passed 32 tests each. The PR changes only `runtime/cli_v1/test_mcp_supervised_win32.py`; the runtime source files used by R178 are unchanged between R178's source head and the merged main head. This closes the fake-producer public result-query sequence for that path. It does not upgrade the R178 sample's producer exit from normal to abnormal, and it does not replace a fresh live native trial or the matched #57 efficiency comparison.

Next native evidence should distinguish the R175 abnormal-exit path from the R178 observer-timeout path, preserve the action/cancellation field scopes, and keep one dispatch/no replay plus both horizons and the exact task effect. Any fresh attempt needs its own frozen conditions and packet; R175–R178 are immutable historical attempts.
