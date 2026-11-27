# Result S08

**HOLD — the runner verified and imported Xlib, but the public backend import stopped because Pillow (`PIL`) was missing before any Fake X case ran.** No portability outcome is claimed. S08 was not retried.

The exact saved stderr ends at `ModuleNotFoundError: No module named 'PIL'` while `probe.py` imports `runtime/guarded_x11_v1/bridge.py`. The S08 environment contained only python-xlib 0.33 and six 1.17.0; that dependency bundle did not cover the runtime's image import. The next preparation must inventory direct and transitive imports for the actual import path, pin and hash them, and freeze them before starting another session.

The dedicated WSLc session, pinned image, and no-network container started; the API confirmed the exact container/image/session were deleted or terminated. The unique storage directory contained one `storage.vhdx` (203,423,744 bytes, SHA-256 `fb393ac935735aa02eb2438378b1138121349b8c9440f40ea66d6bcc03404c97`) in the first post-run inspection. By the later cleanup check, the exact path was already absent; no manual delete was performed. This timing discrepancy is recorded in `STORAGE-CLEANUP.json` rather than claiming an operator removal. No global WSLc inventory or Docker was used.

S08 confirms only dependency-path and import progression. It does not establish Fake X case correctness, real X/OS behavior, input release, recovery, app/MAP01 task effect, or computer-control efficacy.
