# #4316 Rung 0: non-authoritative attention cue channel

Allocation `attention-cue-4316-20260924-ac41`; intake main `55d6c6cead19fc02824d620c174bf0fd03681cf1`.
Own only `research/integration/attention_cue_rung0_ac41_v1/**` on `research/attention-cue-rung0-4316-20260924-ac41`. Keep #4316 open: human/model efficacy is Rung1 and is not measured here. #2755 detector attribution and #4318 snapshot-cut allocations are untouched. Prior conversation-local pilots and their HOLDs are not rerun, pooled or retroactively registered.

## H
A dedicated scripted stdin cue can select real X11 image history/ROI without application task input or authority. Invalid scope/time/ROI/schema must ignore the hint while preserving autonomous observation. Incomplete history must remain explicit. This is the native-acquisition-to-bounded-packet engineering rung, not an empirical human-attention benefit claim.

## T
Twenty fresh sessions: ten conditions, two repetitions. Four immutable five-case batches, one invocation each, in the order declared in source/run.py. Names: NO_CUE, VALID, OLD_GENERATION, FOREIGN_SESSION, WRONG_SURFACE, FUTURE_TIME, EXPIRED_TIME, ROI_OUTSIDE, MISSING_HISTORY, AUTHORITY_FIELD. All share a fresh authenticated, TCP-disabled Xvfb and a separate cooperative Xlib app. A separate engine subprocess receives scripted cue bytes through stdin, never an application-visible key. No human participant, model/provider, keyboard/mouse/XTEST, host desktop/user data, package install or experiment network.

The app draws states1,2,3 under explicit acknowledgements. The observer acquires three actual 64x48 depth24/32-bit little-endian ZPixmap images. It then inspects app state/input, submits the cue, reinspects and captures a fourth unchanged-current witness. App remains quiescent during cue handling. Frames carry a fixture-authored observation-stream generation3; frame IDs1..3 are separate from that stream generation. This is neither X event serial nor authenticated generation discovery.

At most three16x16 four-byte-per-pixel patches are output in ALL conditions. Cue-free and invalid-cue fallbacks use ROI[0,0,16,16]; valid cues use[32,8,16,16]. In MISSING_HISTORY the engine receives only the actual last frame; it must not fill the two missing older frames. Maximum decoded image bytes3072, Base64 image bytes4096, excluding separately reported JSON metadata. Full-frame acquisition cost remains present; no capture-cost or task benefit is claimed. The two-second maximum cue age uses same-host monotonic clock; expired/future timestamps are explicit test-field perturbations, not measured natural delay distributions.

Supplied Linux/CPython3.13.5/Xlib0.15/Xvfb; actual ENVIRONMENT.json retained. Docker CLI/image attestation absent; no Docker/OrbStack equivalence. Pixel ABI is explicitly required; incompatible layout stops. Source, expected gates, auditor, controls and environment are publicly frozen/read back BEFORE formal batch0. Excluded construction b0 failed before packaging (native reply str->bytes); b1 uses exact Latin1 conversion and passes3 cases. Original b0/source/error remain. Unit methods12 and construction effective mutations12 pass before freeze.

## D
PASS_CUE_CHANNEL_RUNG0_SCOPED requires all20 expected sessions, four actual batch exits0 and60 named actor/engine/server exits0; native image bytes and exact crops independently reconstruct; output dispositions agree with the frozen conditions; invalid hints use ordinary fallback; history availability is truthful; all app before/after state3, input events empty, last pixels unchanged, X-server keymap/button state neutral; authority_granted=false/action=null/lease_extended=false throughout; private displays cleaned; source hashes match; separate raw-only audit errors=[] AND12/12 actual changed control payloads reject without parser fallback/crash. The total decision is joint; audit.json alone does not waive controls.

Exact expected condition counts: NO_CUE2, accepted VALID2 and MISSING_HISTORY2, ignored invalid hints14; missing-history packets2 contain only one patch. No probability or human/model attention endpoint is estimated. Complete violation is FAIL; missing evidence, unsuccessful timing exposure, partial batch or ineffective controls is HOLD/STOP. No batch retry/replacement/exclusion/post-result tuning. A consumed native run is never rerun for packaging or CI.

## C / U
Cooperative app, scripted cues, trusted current metadata and complete unobscured frames. No source authentication, arbitrary app, real human operator, semantic ROI interpretation, continuous autonomous task completion, dynamic source replacement race, hard deadline, cross-platform safety, production API or model/token/latency benefit. The engine deliberately has no task-input backend; that is architectural separation, not containment of hostile code. The same-author separate audit is not external human review. Clock scheduling/transport overhead is not calibrated; combined timing uncertainty and coverage factor are unavailable and not fabricated.

## Variable / field table and unit check
| Symbol/field | Meaning (Japanese) | SI unit | Definition | Domain / assumptions | Type |
|---|---|---|---|---|---|
| x,y | 画像内の切出し原点 | 1 | roi[0:2], discrete pixel indices | nonnegative, contained in64x48 | integer scalars |
| w,h | 切出し幅・高さ | 1 | roi[2:4], discrete pixel counts | integers1..16, contained | integer scalars |
| emitted_ns | 注意喚起の生成時刻 | s | stored integer ns, multiply by1e-9 for SI | same monotonic clock domain | integer scalar |
| checked_ns | 包装器の判定時刻 | s | actual monotonic_ns at handler | same clock, >=capture | integer scalar |
| captured_ns | 各画像の取得完了時刻 | s | monotonic_ns after actual XGetImage | increasing within session | integer scalar |
| generation | 観測ストリームの世代 | 1 | fixture current generation3 | exact integer, bool rejected | integer scalar |
| surface | private X11 window identity | 1 | actual created window XID | exact scope, not authority | integer scalar |
| decoded_bytes | 出力画像バイト量 | 1 | frame count times width times height times4 octets | <=3072, metadata excluded | integer scalar |

Unit check: timestamp differences remain seconds after ns-to-s conversion. Pixel and frame counts are dimensionless; multiplying by four octets per pixel yields octet count, not physical area or elapsed time. This run has no calibrated latency benchmark.

## Conditional reasoning
The finite field validation rejects an invalid cue before assigning its ROI. The default ROI is preserved on rejection. Each selected source frame contributes exactly one crop; missing frames cannot be manufactured by that loop. Each crop contains at most16 rows of16 pixels of4 octets, and selection contains at most3 frames. Output capability fields are constants and the engine has no native input call. These code properties do not prove producer truth or human usefulness. The experiment tests their composition with actual X11 capture, IPC and unchanged app effects.

## Roadmap / references
Construction -> public exact source/gates/readback -> four first-outcome native batches -> independent audit/12 effective controls -> complete additive evidence PR -> exact-head applicable CI/review -> qualified main readback. Rung1 and global ROADMAP remain open.
Primary API references: X.Org XGetImage manual (X11R7.5, specified drawable rectangle; obscured pixels are not guaranteed); Python3.13 subprocess documentation (communicate/actual return codes). These explain APIs, not this experiment's outcomes.
