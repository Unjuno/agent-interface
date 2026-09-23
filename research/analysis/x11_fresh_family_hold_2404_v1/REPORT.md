# Fresh X11 visual-family transfer — HOLD

## H/T/D/C/U

- H: bounded shift adaptation (#2399) may transfer to a genuinely fresh X11 visual family.
- T: train on fixed 160 base frames plus 80 old shift-adaptation frames; evaluate only 160 fresh X11 frames with grid background, elliptical 64×40 target, random placement, clutter, and periodic occlusion. Keep the 354-parameter CNN and conservative gate.
- D: fresh Docker/Xvfb/Tk/python-xlib frames, 160 unique SHA-256 hashes; old adaptation frames were not used as evaluation.
- C: no domain-generalization, arbitrary GUI, token, latency, gameplay, or runtime claim. Local model has no authority.
- U: accepted false positive is FAIL; no accepted fresh samples with safe behavior is HOLD.

## Result

| metric | result |
|---|---:|
| fresh rows | 160 |
| accuracy | 50.0% |
| false positives | 0 |
| accept / YIELD / reject | 0 / 160 / 0 |
| accepted false / true | 0 / 0 |

**HOLD/STOP:** the within-family adaptation improvement in #2399 did not transfer to the fresh visual family. No promotion. All previous results remain unchanged.
