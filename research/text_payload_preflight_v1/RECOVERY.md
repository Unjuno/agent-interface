# Workspace loss and separately allocated candidate-only probe

The original source/plan freeze 22bbaeba28016deda3efb201fe5222ea26dd6fb0 is retained unchanged. Its original 260-trial comparison and six-session formal Writer transfer did NOT start. The outer launch helper completed unit tests but failed while querying missing python-xlib distribution metadata, before spawning the GUI command. Subsequently /mnt/data/text-payload-work disappeared and the container showed a fresh /mnt/data mount at 2026-09-15 19:30 UTC.

Raw development traces, development Writer ODTs and the first unit log are unavailable after that workspace loss. DEVELOPMENT.md and the conversation tool outputs describe witnessed development runs but are NOT byte-reconstructible retained GUI/Office evidence. Do not count them as a retained formal pass. The GitHub source freeze survived; no old formal GUI ID was executed or rerun.

## New finite recovery allocation

Result ID: text-payload-candidate-recovery-v1-20260916-01.
New source: recovery_probe.py. Unchanged dependency blobs enforced by runner: preflight.py 35c7375e50f3e0c58f57c8139a6dc8abeef87771; receiver.py decce092c4f5b4d93031059c5ecb84151e11f8b8; test_preflight.py d98aaa58dcd3a5b5ef84d3441d895de45e62431e.
H: the unchanged candidate provides exact printable-ASCII delivery and rejects nonprintable payloads before any input in a fresh private X11 fixture.
T: 13 unit tests; one candidate-only real-X11 run of 128 payloads ('office' + code point 0..127 + 'tail') and four context negatives (stale observation/binding, expiry, wrong target). All 132 rows retain receiver text/events and map/clipboard/physical-state receipts. Authenticated Xvfb 1024x768x24, Openbox, separate-process Tk receiver, constant 12 ms pacing. No baseline, no formal Office, no model/provider call. Prior development data are excluded.
D: PASS only if 95 printable payloads are exact, 33 control payloads and four context negatives have zero injected input/receiver effect, and all 132 map/clipboard/release controls pass. Failures are retained; this result directory is exclusive and never reused. This is finite conformance, not statistical reliability or a speed benchmark.
C/U: first-group two-level default X map, a single private host and supplied freshness counters. No Unicode/IME, generic ASCII control-character support, arbitrary XKB layout, atomic rollback, shared-runtime/native systems implementation, or three-OS support claim. Original comparative and Office formal plans remain NOT EXECUTED. The recovery is not a replacement measurement for a missing original outcome.

Run once from repository root using a new absolute output directory:

```sh
xvfb-run -a -s '-screen 0 1024x768x24 -nolisten tcp' env AGENT_INTERFACE_PRIVATE_XVFB=1 python3 research/text_payload_preflight_v1/recovery_probe.py --source-commit <recovery-freeze-SHA> --out /absolute/new-recovery-result
```

A rejected placeholder PR attempt before branch creation returned HTTP 422; no placeholder PR was created. Direct raw source download attempts were unavailable; exact source bytes were recovered from connector-visible content and verified by their original Git blob IDs.
