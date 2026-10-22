# Visual-context-staleness A01 scope

This boundary test distinguishes image identity from typed HUD/focus freshness. The source and changed frame are exact adjacent retained PNGs, and the typed event rows are copied from the frozen current-main raw log. The paired monitor sees the actual `frame_rgb_sha256` metadata but only evaluates paired health/ammo validity. The pending model transport and response are synthetic; the test does not show that the frame change represents a threat or that an executor-ready action is wrong.

The retained live trace came from an earlier controller source whose hash was not included in its runtime source manifest. It is used only as a real observation fixture. The code under test is extracted byte-for-byte from current main `f185a9059d485a4f8d5a65e9e7f6782897f67eae`. This is construction/replay evidence, not current-main live-game evidence.
