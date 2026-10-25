# Win32 Freedoom MAP01 live probes — 2026-10-26

## Disposition

Five separate local Windows attempts are retained. R01 stopped on startup/observation setup before MAP01. R02 produced one visible forward scene change and a verified Win32 `release_all` receipt. R03 showed continued application-view motion after that receipt and failed its preregistered sampled-settle gate. R04 stopped before capture when its harness imported an unavailable `psutil` dependency; it sent no input and is retained as a setup failure. A fresh R05 no-input control found at most 72 changed world pixels between +1 s and +2 s, compared with 101,071 in R03. Do not pool these attempts into a reliability estimate.

The source runtime tree was identical to the recorded `origin/main` tree at `7f518bc2982165e2e4c142d8ed71cfb0515d4362` (`ac30a08b21e4c915417589f26f83352e516c21d7`). The ViZDoom executable and Freedoom 2 IWAD are locally retained dependencies; their SHA-256 values are in each frozen preregistration and private custody packet.

| Attempt | Observed result | Decision |
|---|---|---|
| R01 startup probe | `-help` opened an IWAD selector and reached credits, not MAP01. ENTER and SPACE each returned a scoped verified release receipt; the credits frame did not change. `PrintWindow` was black while `screen_physical_px` showed the credits. | Setup/observation-path stop; says nothing about playable-scene input. |
| R02 direct MAP01 | One 300 ms UP input was accepted/completed. The receipt reported all keys/buttons up and known. A 640×480 image changed by 226,727 RGB pixels; review showed forward corridor motion. First postflight began 203 ms after the receipt. | Scoped live input, environment response and runtime-release evidence. Does not establish when the game view stopped changing. |
| R03 release horizon | Fresh MAP01 process, one 300 ms UP input, verified all-up receipt. World-region change was 39.48% from +1 s to +2 s and 0.102% from +2 s to +5 s. | Preregistered sampled-settle gate **FAIL**. View was nearly stable by +5 s; exact stop time and cause are unresolved. |
| R04 idle-control setup | Python capture harness stopped before first image because `psutil` was unavailable. Zero capture and zero input; exact test process/window closed. | Preserved setup stop; no environmental result. |
| R05 idle control | Fresh MAP01 process, no runtime or Computer Use inputs. Consecutive world-region changes: 115 pixels baseline→+1 s, 72 pixels +1→+2 s, 68 pixels +2→+5 s. All three are below 1%; images show the same viewpoint with minor animation. | `PASS_SCOPED` for sampled idle stability in this one control. This makes ordinary idle animation unlikely to explain R03's large +1→+2 s change, but does not establish causality or a continuous-time stop bound. |

R02's later observations were first labeled as +750 ms/+1750 ms but were actually +36.406 s/+37.484 s after release. An additive timing correction preserves the original raw bytes and removes the bounded-stop interpretation. R03 is a new process and attempt, not a repair or pooled replicate.

## What this establishes

- Current-main `Win32Backend` / `Win32RuntimeSession` can produce one visible forward movement in a correctly launched local Freedoom MAP01 process, with a scoped verified runtime release receipt.
- A runtime all-up receipt is not evidence that the application view is already settled. In R03 the view changed substantially between the +1 s and +2 s samples after the receipt.
- The R05 no-input control changed only 72/256,000 world pixels (0.028%) from +1 s to +2 s. Compared with R03's 39.48%, the large R03 scene change is unlikely to be ordinary idle animation in this one fresh-process sample. This is a cross-attempt inference from one observation per condition, not a randomized paired causal result.
- On this D3D window, `screen_physical_px` was readable where `window_client`/`PrintWindow` returned black in R01.

This does not establish physical key-state release timing, bounded release under blocked platform I/O, bounded recovery, standard V39/public-caller integration, independent MAP01 task success, a continuous-time stop bound, model/provider behavior, matched efficiency, or reliability. Runtime `task_success` is null in the playable-scene attempts. No WSLc allocation or Docker operation was used. Shared WSLc authorization remains governed by the separate STOP/HOLD record.

## Private raw custody

Exact BGRA frames, PNGs, controller records, preregistrations, timing correction/audit and cleanup receipts remain in the local private packets named in [PRIVATE_CUSTODY.md](PRIVATE_CUSTODY.md). The five SHA-256 manifests cover 19, 16, 26, 5 and 16 files; their manifest digests are recorded there. Raw images and host-specific paths are not copied into this public research tree.

All five test-owned processes/windows were closed and checked absent. Each packet retains its cleanup receipt. R01–R03 each sent only the preregistered task inputs. R04/R05 sent no task input; Alt+F4 was used only for exact-process cleanup after the observation/setup phase.
