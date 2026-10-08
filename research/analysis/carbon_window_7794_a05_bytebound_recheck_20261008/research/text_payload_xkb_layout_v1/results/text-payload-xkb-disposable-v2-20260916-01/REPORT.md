# XKB disposable-server layout transfer v2 — retained result

**Result ID:** `text-payload-xkb-disposable-v2-20260916-01`  
**Source/plan freeze:** `c057c94f09a277f35e809aecc3739c294c2364dc`  
**Prior formal result:** `text-payload-xkb-layout-v1-20260916-01` — retained fixture-restoration FAIL, never rerun.

## Disposition

**PASS_SCOPED_PAYLOAD_KEYMAP_TRANSFER / REQUIRE_PAYLOAD_KEYMAP_PREFLIGHT / HOLD_FULL_XKB_AND_PRODUCT_PROMOTION**.

The v2 allocation executed once. It changes only the fixture isolation contract from v1: every arm runs in its own fresh authenticated `xvfb-run`; fixture keymap projection is applied before candidate delivery; candidate map invariance is measured during the arm; the X server is discarded after the arm. No in-server restoration claim is made.

## Result

| projected condition | exact accepted | zero-input rejected | trial gate failures |
|---|---:|---:|---:|
| US | 95 | 0 | 0 |
| German | 85 | 10 | 0 |
| French | 85 | 10 | 0 |
| US Dvorak | 95 | 0 | 0 |

Across all four arms: **360 accepted characters were exact**, **20 rejected characters produced zero input and zero application text**, and all **380/380** trial gates passed. Candidate map fingerprint remained unchanged for all 4 arms and physical input ended empty for all 4 arms.

German safe-refusal set: `@[\]^` + backtick + `{|}~`.  
French safe-refusal set: `#@[\]^` + backtick + `{|}`.

These refusals are the main architectural result: printable ASCII is not a single direct-key capability bit under this candidate. Eligibility is payload × live-keymap. A nonrepresentable character is refused before input rather than silently guessed or routed through a side-effecting fallback.

## Retained v1 failure

The predecessor formal result remains **FAIL_FORMAL_FIXTURE_RESTORATION_GATE**. All of its per-character delivery/refusal gates passed, but `XChangeKeyboardMapping` fixture setup could not restore the original Xvfb core map byte-for-byte: a saved 7-wide map normalized to 15-wide. V2 does not relabel that failure. It allocates a new process-isolation question and destroys the mutated private X server after each arm.

## Evidence closure

- source readback: 8/8 relevant local blobs match frozen Git blobs;
- formal static tests: 3/3 PASS;
- formal GUI matrix: one execution, 4 private Xvfb arms, no arm reruns;
- aggregate SHA-256 `a9d4da9eb701e2e050e45a635e94cc786620178dfe0c9cf341da0ecba62403d1`;
- full aggregate is retained as exact deterministic gzip/base64 alongside the independent audit;
- model/provider/network calls: 0.

## Scope limits

This is **not full XKB**. The fixture resolves standard XKB definitions but projects only Group1 level 0/1 into the core keyboard map. AltGr, extra groups, types, dead-key composition, IME, locale behavior and physical hardware layouts are not established. The fixture projection itself is a global mutation inside the disposable X server and is not a product delivery mechanism. No Office, Wayland, Windows/macOS, model/token, end-to-end speed or reliability claim follows.

## Architectural implication

Keep semantic `text` intent independent from lowering eligibility. A direct-key route should preflight the concrete payload against the current keyboard map and fail closed before input if the whole payload is not representable. Fallback to clipboard/accessibility/IME remains a separate route decision with explicit side effects; it must not be triggered blindly after partial direct-key execution.
