# Fresh source-first Inkscape ABI-v2 live semantic reproduction v1

Task: `O3-INKSCAPE-ABI-V2-SOURCE-FIRST-LIVE-20260916-011`  
Issue: #217  
Immutable base: `cc1719d6bd07e81c8cc1e928177b903e06271c37`  
Formal seed: `994601`

## H

#215 invalidated the old PR #168 live result as source-bound/reconstructible evidence. This experiment therefore creates new live evidence against the current retained ABI-v2 bytes rather than relabeling the old result.

The question is deliberately narrow: can current bridge-v2 + normalizer-v2 consume a real Inkscape/X11 authority-expiry trace produced by a source-first standalone authority harness?

## Frozen sources

The formal runner was committed before formal execution.

- `live_runner.py`: SHA-256 `0cfb81a08c8387c6bddcbb3d35017fb4681d9c337a28fb62162dfd17a12243b2`; Git blob `b6d9fd72f74f32281deed9b35cc19a8f020e70ef`
- current `authority_ended_bridge_v2.py`: SHA-256 `37e544086fe70087c0a2e6c03ce8c42c1c5dd71989f7fe541eb9055b3551eb52`
- current `post_authority_normalize_v2.py`: SHA-256 `dc664652c7c29b002005feb7b69122d29619a449c6ad781a65ac5abfaa186d41`

The container-reconstructed runner Git blob matched the committed GitHub blob before execution.

## Formal setup

Environment: Inkscape `1.4 (e7c3feb100, 2024-10-09)`, private Xvfb display plus openbox. `_NET_ACTIVE_WINDOW` was `shape.svg - Inkscape` before input.

The internally generated runtime authority identity was `901e6ed15b87454fdbef7909c1e0f026`. The harness admitted one `Shift_L` press with a planned 1500 ms hold and a 500 ms authority deadline. The planned tail text was `999` and was never admitted.

After deadline, the harness released Shift, verified the X server had no keys or pointer buttons down, then performed exactly two passive 320x240 root observations inside a fresh independent 400 ms lifecycle budget. Those observations were normalized by the current retained normalizer and passed to the current retained bridge.

## First outcome

Result ID: `inkscape-abi-v2-source-first-live-v1-20260916-994601`  
Formal retries: **0**  
Hard gates: **9/9 PASS**  
Decision: **`RETAIN_SOURCE_FIRST_LIVE_ABI_V2_SEMANTIC_REPRODUCTION`**

Observed facts:

- active window was Inkscape before input;
- X keymap observed `Shift_L` down after the one admitted press;
- authority deadline was `7641123188949 ns`; expiry was detected `16.542996 ms` after that deadline and still about `983 ms` before the planned 1500 ms hold end;
- release verification reported `keys_down=[]`, `buttons_down=[]`;
- post-authority captures were sequences `[2,3]`, selected `3` with rule `latest`;
- lifecycle slack at snapshot completion was `343.738753 ms`;
- both post-authority capture hashes were identical: `6376a77148ff0f5d859d94b04ff7973f957a791f38599e1dc982876aa5a2009f`;
- `post_release_input_admissions=0`, `steps_completed=0`, `tail_program_steps_resumed=0`;
- bridge gate passed `safe_yield / authority_unavailable / completed_actions=0`;
- SVG SHA-256 before and after remained `a54fa1127a48926bd239844634a05c81f11bedf06c1e3bda60277347684da7ad`; no tail text `999` appeared.

Formal-result SHA-256: `402f6320f7a87acd0540b9aab1cd2eee610fab73c9937c72a682b77f11e0e9f3`. Event-trace SHA-256: `2504944decd52136ae773417f93d47542820a35864d0a8bc51f1f66d8017fe77`.

## Independent audit / recording defect

The formal runner has one evidence-recording defect: it first stored the raw bridge decision under `decision`, then reused the same key for the experiment-level decision string. The live gate itself compared the raw bridge return value before that overwrite, so the gate result remains meaningful, but the raw return dictionary was not preserved in `formal-result.json`.

No formal retry was performed. Instead, the independent audit reloaded the current byte-exact bridge and re-evaluated the retained formal receipt. It recomputed:

`{"status":"safe_yield","reason":"authority_unavailable","completed_actions":0}`

The independent audit passed with zero errors.

## D

Retain this result as a **fresh source-first live semantic reproduction for the current ABI-v2 contract**. It repairs the specific evidence gap that the current bridge/normalizer bytes previously lacked trustworthy source-bound live evidence.

It does **not** restore the old PR #168 formal result, and it does not prove the full retained servo/executor path. #215 remains correct: the old run is still not source-bound/reconstructible evidence.

The evidence hierarchy is now:

1. old PR #168 live observation: historical raw observation only;
2. current ABI-v2 semantic/offline evidence: retained;
3. this experiment: fresh source-first real-Inkscape semantic reproduction against exact current bridge/normalizer bytes;
4. full project runtime integration and crash-after-send: still unproved by this experiment.

## C

The live authority scheduler here is a standalone X11 harness, not `cause_servo_*` / executor production composition. A bounded 320x240 root observation was used to stay well inside the independent lifecycle budget. The deterministic runtime-owned intent token is an evidence identity, not a cryptographic trust root.

## U

The next high-information step is not another ABI semantic rerun. It is to feed this retained live receipt/terminal through the current identity-binder + byte-pinned durable-issuance composition and verify restart/consume behavior without another GUI allocation. Only after that should a full retained servo/executor live integration be considered for crash-after-send work.
