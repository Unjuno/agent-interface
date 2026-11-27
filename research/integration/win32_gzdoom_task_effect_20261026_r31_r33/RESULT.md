# GZDoom MAP01 public-control diagnostic R31–R33

**Outcome: task effect failed in all three attempts.** Each attempt used a fresh GZDoom process and target generation on the user's Windows PC. The standard public MCP dispatch completed, emitted two input events (down/up), returned a verified terminal release receipt, and passed a same-generation neutral completion readback. No attempt established an application effect or level completion.

| Run | Action | Input dispatch / release | Independent pixel effect |
|---|---|---|---|
| R31 | `UP` down, 300 ms, `release_all` | dispatched; release verified | 316/1,003,200 pixels = 0.031499%; failed >5% |
| R32 | configured forward key `W` down, 1,200 ms, `release_all` | dispatched; release verified | 316/1,003,200 pixels = 0.031499%; failed >5% |
| R33 | configured `Tab=togglemap`, 150 ms, `release_all` | dispatched; release verified | 316/1,003,200 pixels = 0.031499%; automap absent; failed >5% |

The three changed-pixel masks are identical, not merely equal in count: all 316 pixels lie in x=524..539, y=425..445. This localized recurring change is consistent with a small animated panel and does not show movement or automap activation. The conclusion that the actions had no visible task effect is based on both the frozen pixel oracle and screenshot review; it does not identify whether the cause is focus, game input handling, injection, a paused state, or capture semantics.

R31 used `UP` before checking the live config; R32 then used the confirmed `W=+forward` binding and remained ineffective. R33's `Tab=togglemap` positive-control also remained ineffective. The retained public call reports are authoritative: an early derived summary in each packet incorrectly selected a nested `input_dispatched=false`; additive `RECONCILIATION_R31.json`, `RECONCILIATION_R32.json`, and `RECONCILIATION_R33.json` correct that field without modifying original raw evidence. The R31 cleanup wait used an access mask without `SYNCHRONIZE`; post-run inventory confirmed that exact PID exited and the two prior UNKNOWN PIDs remained alive. R32/R33 exact-process cleanup passed.

The earlier successful public forward-effect result R12 targeted a window titled `VIZDOOM 1.3.1 (ZDOOM 2.8.1+)`, not this GZDoom target. It therefore does not establish GZDoom input acceptance.

All raw dispatches, process identities, configs, frozen conditions, producer receipts, baseline/post-action pixel buffers, PNGs, and additive reconciliations remain in the local evidence packets:

- `private-packets/map01_native_windows_20261026_r31`
- `private-packets/map01_native_windows_20261026_r32`
- `private-packets/map01_native_windows_20261026_r33`

R33 also preserves its preflight-only `user33` harness typo and the corrected frozen runner. No WSLc allocation, Docker operation, or model call was used. R27/R28 PIDs 21660/6696 remain intentionally preserved as UNKNOWN; this work does not resolve them.

**Next discriminating work:** inspect why the standard SendInput path yields verified API emissions and neutral release yet produces no change in this GZDoom target, then use one new process generation with a target-response observation that distinguishes focused input delivery from background/pause/capture behavior. Do not replay R31–R33.
## Source-path follow-up

The installed executable reports `g4.14.2-m` (SHA-256 `ec706c2ea1ef946eec13be7b1b461df8d52efcd47caa6c056ed0e0257f7f9ffa`). The matching official GZDoom `g4.14.2` source prefers `FRawKeyboard`, registers it with `RIDEV_INPUTSINK`, and falls back to DirectInput only if registration fails ([keyboard startup and raw registration](https://github.com/ZDoom/gzdoom/blob/g4.14.2/src/common/platform/win32/i_keyboard.cpp#L439-L451), [fallback selection](https://github.com/ZDoom/gzdoom/blob/g4.14.2/src/common/platform/win32/i_keyboard.cpp#L565-L577)). Its window procedure routes `WM_INPUT` to `ProcessRawInput`, while the ordinary keydown cases do not dispatch game keys ([raw path and keydown handling](https://github.com/ZDoom/gzdoom/blob/g4.14.2/src/common/platform/win32/i_input.cpp#L335-L359), [keydown cases](https://github.com/ZDoom/gzdoom/blob/g4.14.2/src/common/platform/win32/i_input.cpp#L436-L450)); the base window-message hook returns false ([default hook](https://github.com/ZDoom/gzdoom/blob/g4.14.2/src/common/platform/win32/i_input.cpp#L777-L780)). Microsoft documents Raw Input as device-specific data delivered through `WM_INPUT`, and `SendInput` as synthetic events inserted into the system input stream ([Raw Input](https://learn.microsoft.com/en-us/windows/win32/inputdev/about-raw-input), [SendInput](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput)).

This makes a Raw Input versus synthetic-input mismatch a strong explanation for R31–R33. It remains an inference: the exact running GZDoom process's successful registration/fallback mode was not observed, and the executable's `-m` build is not proven byte-for-byte equivalent to the official tag. The next conclusive experiment needs an input path the selected GZDoom backend actually consumes, or a diagnostic build that reports which keyboard backend registered. Do not treat another `SendInput` key or mouse action as a task-effect trial until that distinction is addressed.
