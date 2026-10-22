# Astra MAP01 retrospective video alignment (A01)

This package aligns twelve selected decision screenshots from the failed Astra MAP01 run to its retained 2x MP4 and compares the video HUD around the final health change. It is a retrospective analysis of existing artifacts. No game, model, GUI, or input was rerun, and the selected screenshots are not the original complete frame sequence.

`align.py` extracts the 640×480 game viewport from each video frame, reduces it and the selected screenshot viewport to 160×120, and uses minimum mean absolute RGB error to identify each screenshot's closest video frame. It fits frame number to monotonic capture time by ordinary least squares, then compares the HUD region in video frames 647–708 with the decision 11 (4%) and decision 12 (0%) screenshot references. `audit_alignment.py` independently checks frozen input hashes, sequence-to-frame associations, fit arithmetic, event timestamps, and the direction of each HUD-reference comparison.

The twelve best matches are frames 63, 115, 176, 220, 286, 362, 418, 473, 538, 591, 647, and 708 for sequences 39, 76, 117, 148, 211, 252, 293, 336, 378, 417, 459, and 504. Leave-one-out RMS fit error is 0.297 frame; the largest held-out error is 0.660 frame. The recording is 10 fps at 2x playback, so each encoded frame represents about 200 ms of source control time.

For the HUD region, frames 647–702 are closer pixelwise to the 4% screenshot reference; frames 703–708 are closer to the 0% reference. The interval from frame 702 to 703 straddles the controller model end and action acceptance when mapped through the fitted alignment. This narrows the earlier 12.16-second observation gap to a transition near the control boundary, but does not establish whether death happened before or after model completion/acceptance, nor identify its cause. MP4 compression and frame sampling limit precision; this analysis does not recover exact intermediate PNGs.

Reproduce on macOS with Python 3, Pillow, and ffmpeg:

```sh
python3 research/doom/map01_astra_video_alignment_a01_20261005/align.py
python3 research/doom/map01_astra_video_alignment_a01_20261005/audit_alignment.py
```

The local attempt used the desktop bundled Python runtime (Python 3.12, Pillow 12.3.0) and host ffmpeg. Docker was available for `docker ps`, which showed no running containers; `docker image ls --digests` failed with a containerd blob error (`operation not supported`). No Docker experiment was run. This is offline posthoc media analysis, not the isolated-X11 live experiment allocated by Issue #5156.
