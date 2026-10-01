# OpenTTD coordinate-frame resolution transfer v1

This study tests whether a known OpenTTD pointer plan and its path-derived local
condition can transfer from a 1024x720 application window to new resolutions
without inspecting and manually correcting the new screen first.

The first Windows-Python command stops during import because the Linux caller
requires `fcntl`; OpenTTD never launches and no fresh input occurs. The unchanged
preregistration and source hashes are then executed through WSL Python. The
pre-input failure is retained as `preflight-windows.json`.

The first preregistered 1280x720 study applies `dx=+128` globally, assuming the
wider viewport moves all content right by half the width increase. The repeat
stops, but the target changes only 14 monitored pixels and remains incomplete.
The 63 exact frames are retained as a failed transform.

The archived pointer bindings expose the opposite window-origin delta: the
1024x720 window is `[129,40,1024,720]`, while 1280x720 is
`[1,40,1280,720]`. A second preregistered study therefore applies `dx=-128`
globally. The map path reaches the intended area, but the toolbar controls have
not moved with the window origin. The target changes 286 target and 132 guard
pixels, stops as `guard_changed`, and remains independently incomplete. Its 67
exact frames are also retained.

The failures show two coordinate frames. Saved map content is window-relative
and follows the origin delta. Centered application chrome remains at the same
absolute screen coordinates when the window width changes. The third study
freezes these transforms separately:

- `screen_chrome`: `dx=0`, covering the Road Construction and road-direction controls;
- `window_content`: `dx=-128`, covering the map drags and boxes derived from them.

At 1280x720, the repeat returns `target_not_reached`, suppresses the continuation
and independently remains false. The target returns `met` with 168 target and
one guard pixel per sample, executes the continuation and independently completes
the guarded five-tile L. Both allocations release input and preserve forbidden
and surrounding tiles. The corrected pair contributes 67 exact frames.

A preregistered 1152x720 replication predicts its window at
`[65,40,1152,720]` before launch. It keeps `screen_chrome dx=0` and uses
`window_content dx=-64`, reversing the allocation order. Target and repeat again
classify2/2 and agree with the independent engine score. The predicted binding
matches the observed binding and all68 frames replay exactly.

Across the two corrected resolutions, positive/repeat classifications are4/4
over135 exact frames. Including the two retained failures, the cross-OS audit
replays265 exact frames. Drag-to-local-condition time is 2.457–2.600 seconds, so
the transfer does not improve interaction tempo.

`coordinate_frame_transform_v1.py` records the discovered distinction as a
strict pure API. It derives window-content translation from source and target
binding origins, keeps explicitly screen-fixed chrome unchanged, translates
ordered points and refuses malformed geometry, points and unknown frames. The
current live studies still declare frames in their task code; automatic frame
classification and runtime integration remain open.

Decision: retain the frame-specific transform as a scoped resolution-transfer
candidate. Next integrate explicit coordinate-frame identity into admitted
pointer intents and obtain the target binding live, then test a new save or a
changed viewport state. These runs use one development-known seed and scripted
paths; they establish no model, unseen-task, token, human-speed or broad layout
generalization claim.
