# Premeasurement commitment — #2117 receive/hash factorial allocation03

Created before formal case0. Allocation `receive-hash-handoff-20260922-03`; intake main `1f798cbb60b929e738c6bf8a5912470b38b45ff4`. This is execution engineering for the existing scientific question under #2117, not a wrapper-only successor Issue. Preserve allocation01 13/32 HOLD and allocation02 3/32 STOP unchanged; no old cases pooled or completed. #4010/PR4025 already owns validation-completion freshness semantics and is not rerun.

## H / T / D / C / U

H: under a busy consumer-interpreter Python thread, bounded native receive batching plus four1024-byte SHA256 updates improves20ms validation-completion coverage by >=25 percentage points over individual receive/whole4096-byte SHA256, reduces the median of case-median capture-to-validation ages to <=0.5, and loses <=5 percentage points of idle coverage. Every policy/load cell must capture >=95% of48 authored cues.

T: unchanged32-case crossed receiver/hash/load schedule, four balanced blocks. Policies single_whole, single_chunked, batch_whole, batch_chunked; idle and busy. Block0/2 load order idle,busy; block1/3 busy,idle. Policy list is left-rotated by block index. Each case600ms,12 nominal5ms cues at60ms+i*40ms,2ms nominal acquisition with skipped missed slots. Fixed32x32 BGRX4096-byte XGetImage ROI at48,48; process-isolated observer in every arm. Capture/sample/delivery/verification/backpressure raw bytes and clocks are retained. Source/native binaries/case constants are unchanged from allocation01/02.

One case per separately supervised invocation, fresh private Xvfb per case. Startup3s + case12s + failure recovery2s + server cleanup3s + bookkeeping reserve2s =22s < worker26s; external waiter31s; outer tool40s. These are operational allowances, not hard-real-time claims. Prefix hashes and exclusive consumed markers forbid replacement or advancing over an incomplete case. Thirty-two commands `python -B invoke.py INDEX`, INDEX0..31 sequentially, in this directory. Initialization: `python -B manage.py init --root "$PWD/formal-03"`. Finalization: `python -B manage.py finalize --root "$PWD/formal-03"`. Independent audit: `python -B audit.py --root formal-03 --out reports/AUDIT.json`; copied-evidence controls: `python -B controls.py INDEX`, INDEX0..7. No consumed allocation rerun.

D precedence: any source/raw/type/clock/process/exit/cleanup error -> HOLD_EVIDENCE_INCOMPLETE; any actual cue exposure outside4–8ms -> HOLD_CUE_INTEGRITY; any cell source-cue coverage<95% -> HOLD_SOURCE_COVERAGE; only then H thresholds -> PASS_RECEIVE_HASH_HANDOFF_SCOPED, otherwise HOLD_RECEIVE_HASH_GAIN_NOT_ESTABLISHED. Busy thread CPU exposure must exceed150ms per case. All32 cases,32 observed worker/server exits,8 rejecting copied-evidence controls and zero authority/input/model calls are required. Complete scientific HOLD ends the comparison; no further allocation just to obtain PASS. First infrastructure failure stops immediately with partials, no retries/replacements/exclusions/tuning.

C: Python re-entry, socket scheduling, FFI, hash-update size, buffer/backpressure and host load may explain timing; this is not direct GIL-wait measurement. All captured frames, including unsent ones, remain in coverage denominators. Four case lifetimes per cell are the repetition unit, not thousands of independent images. Prior partial results are known. Server lifetimes and CPU differ from predecessors, so this is not a same-host or uninterrupted-run equivalence claim.

U: provided Linux x86_64 execution container, CPython3.13.5, GIL enabled, OpenSSL3.5.5, AMD EPYC9V74 guest; five logical CPUs allowed with four-CPU cgroup quota, frequency/host load unpinned. Consumer/observer/fixture/Xvfb/load CPUs0/1/2/3/4. Same-container CLOCK_MONOTONIC ns; BGRX depth24/bpp32/stride128/LSB explicit mask guards. Docker/OrbStack/image identity unavailable; not attested network-none. No installs, experiment network, model/provider, XTEST/keyboard/mouse, host display, user data or shared runtime. No model consumption/task utility, tokens, human tempo, general GUI or production claim. #2117 and the full roadmap remain open regardless of component result.

## Excluded construction

35 transport/native-receiver/synthetic-envelope/source-continuity/budget tests passed; one static Xvfb source-pixel/clock/cleanup probe passed with observed server exit0. No new short-cue or load comparison was used as construction. Eight raw-evidence corruption cases are frozen for after the formal audit. Scientific audit body is byte-identical to allocation02; only batch envelope, identity and case path mapping changed.

## Immutable pre-execution identities

Local FREEZE.json created2026-09-21T20:45:06Z; SHA256 `8d91906ab7b6e616a469db2c7646660cfecda3ce43d807d56e367807ca853953`. Full frozen bytes will be delivered with evidence. This commit publicly commits their hashes and gates before measurement, not the full source bytes at this stage.

|File|SHA256|
|---|---|
|ENVIRONMENT.json|2546af96bd03e8da8e0f7af4c38e5276f0b3634480f14749e2a1a688c44de20a|
|PLAN.md|2d8fcdf40202b3466a836e3aafa5727b6d06831f71c067d1d17948674ce64d3a|
|SOURCE_CONTINUITY.json|e7f08e18b55fa27f221d31231c9b74839591739e2a61363d172b0f94b7591944|
|audit.py|8d8ff8757f8308de0db1c1f2fca8acd207cb98adb7fc30a83c9441345a856448|
|build/native.so|e4b6d268a670005c6f5646db9c73786e6092688e25b3ea56c2f1fcf951df67cd|
|build/receive_batch.so|753bc12f59bf75c5f7d12596f63ebe44d71dd84526b2f70d1b4c9bce51c0e2db|
|controls.py|44785879c798344f9135f20851c1f7d752348c9aa78eb3171f60d24976771b8b|
|invoke.py|0d1370af868c662a86f81c9159830d4fded0c4496ff2e6cdf5c0579c84c4bce5|
|manage.py|ea46d91bf503cda65c15efacfbc948ce3663eccca407f21d972bc08d328d136a|
|native.py|f025f0f0c08f1019159cd24620feac5669f5ff5b026213bcaa3bce4c2799673d|
|receive_batch.c|c30bd022ec551f5d89b41b8657fa066aeb4883d80591527c927ae2e5d32a6439|
|receiver.py|d311c1849d849b2c7c6cd248676045e171d5e0a060c241828e54dc1c5c3fb745|
|run.py|f09e9fe0bc61ba67b04b29679c90acaaa0b8b50c36b078c82403729c6e2c1962|
|test_envelope.py|d1332d43fab78d5706b3a4fee07a03550539f100e7ede8e9bc7f6d1a058133c6|
|test_supervision.py|fdc1170daec245ed2eadf8560c8e7a8acf6723c6f7037e795dfa2990d0593dcf|
|test_transport.py|9a73ba409a79b7cef1f4b6d256bb9365509ab669a6121cdada39fb4184816cd6|
|transport.py|b4ce352c141406a47cebd2f210e997cc74748ae6b461edd2cdce12d699bb8c80|
|upstream/native.c|5297e1252113ab4d91c58bd5e7b9462af155979cc44259d42eb98c0d9ce35975|

Previous conversation ZIPs remain byte-identical: allocation01 `25d1de4ba0a2f6e8e049c645d4b6bc06fd00de0354fd9f763b3f6d3b6ff5fbd2`; allocation02 `a7b60fa0179b476912e49a02557276ec82551c0cc63d3111d85d411c83ec13ed`. They were locally frozen/executed when writes were unavailable, not retroactively GitHub-preregistered.

## Variables and unit check

|Field|意味|SI単位|定義|範囲・前提|型|
|---|---|---|---|---|---|
|capture_start_ns|取得開始|s、保存ns|XGetImage直前|同一単調時計|整数スカラー|
|parsed_ns|検証完了|s、保存ns|inspect戻り直後|取得以後|整数スカラー|
|completion_age|検証時画像年齢|s|上記二時刻の差|非負|スカラー|
|coverage|期限内完了率|1|20ms以内件数／全取得|[0,1]、未送信含む|比率|
|coverage_gain|負荷時の率差|1|candidate minus control|[-1,1]|スカラー|
|age_ratio|ケース中央値比|1|candidate divided by control|分母正|スカラー|
|idle_delta|無負荷率差|1|candidate minus control|[-1,1]|スカラー|

Same-clock ns subtraction has time dimension; division by1000000 converts to ms. Coverage and ratios are dimensionless. Example17000000ns is17ms only at the named endpoint. No calibrated combined uncertainty or coverage factor is invented.
