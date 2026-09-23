# Text observed-prefix resume v1 — retained X11 result

**Result ID:** `text-observed-prefix-resume-v1-20260916-01`  
**Source/plan freeze:** `daecf60811de0acacac115e4e1bc9d0621aa06b4`

## Disposition

**PASS_SCOPED_OBSERVED_PREFIX_RECOVERY / REJECT_SENDER_COUNT_AS_EFFECT_ORACLE / HOLD_PRODUCT_PROMOTION**.

One source-frozen private Xvfb/Openbox matrix executed exactly once: 5 stop positions × 4 fault classes × 3 recovery policies = 60 trials against a separate real Tk consumer.

| policy | predeclared gates | exact final text | refusals |
|---|---:|---:|---:|
| blind full retry | 20/20 | 0/20 | 0 |
| sender-count suffix | 20/20 | 5/20 | 0 |
| observed-prefix suffix | 20/20 | 10/20 | 10 |

`gate_pass` for negative policies means the expected unsafe outcome was reproduced; it is not task success.

## Key discriminator

For every tail-swallow stop, the sender reported one more sent character than the application reflected. Example at stop 5:

- sender receipt: `sent_count=5`;
- reflected text before recovery: `book`;
- sender-count suffix resumed with `eeperoffice` -> `bookeeperoffice` (wrong);
- observed-prefix resumed from reflected length with `keeperoffice` -> `bookkeeperoffice` (exact).

This occurred at all predeclared stops 3/5/8/12/15. Therefore injected/sent character count is not sufficient as an application-effect oracle in this fixture.

## Fail-closed boundary

When an earlier character was swallowed, or the application text was externally mutated, current text was not an exact prefix of the intended string. The observed-prefix policy refused all 10/10 such trials and emitted zero recovery key events. Refusal is a safety result, not task completion.

## Controls

- 7/7 frozen source blobs matched before execution;
- unit tests 6/6 PASS;
- all 60 predeclared gates PASS;
- X keymap unchanged across the matrix;
- every recorded post-trial physical key/button state empty;
- final physical state empty;
- model/provider/external-network calls: 0;
- formal GUI reruns: 0.

Independent same-session audit re-read all 60 rows and reproduced every gate and tail-swallow sender/reflection gap.

## Interpretation

The safe recovery boundary is **observed application state**, not merely local injection progress. A sender-side count can be useful telemetry but must not be silently interpreted as committed application text. Resume is only justified when the observed current value has a verified relation to the intended value; this experiment uses the simplest relation, exact prefix.

## Limits

The receiver's Unix-socket text readback is a research oracle, not a product observation mechanism. Real Office/AX/OCR/DOM observations can be stale, normalized, masked, or ambiguous. This experiment does not provide rollback, does not resolve non-prefix divergence, and does not establish Unicode/IME, Office, Wayland, Windows/macOS, or model/token behavior. Lowercase X11/Tk only.

## H/T/D/C/U

**H:** application-reflected prefix is safer than `chars_sent` for text resume.  
**T:** frozen 60-trial real-X11 matrix with clean, tail-swallow, middle-swallow and external-mutation faults.  
**D:** scoped PASS: observed-prefix exactly recovers all 10 recoverable prefix cases and zero-input refuses all 10 non-prefix cases; sender-count fails every injected tail/middle/external divergence.  
**C:** fixture readback is exact and synchronous relative to product-grade observations; different apps may normalize content.  
**U:** no general state-observation transport, no automatic repair for non-prefix state, no atomic text transaction.

## Successor

Do not implement blind retry after partial text failure. The next useful experiment is to add **observation freshness/identity** to the prefix proof: demonstrate that a stale or wrong-target text observation is rejected before suffix recovery, and measure whether one re-observation after interruption is sufficient on a real Office field or another independently observable application.
