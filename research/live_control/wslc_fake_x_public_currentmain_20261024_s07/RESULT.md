# Result S07

**HOLD — WSLc ran the Python runner, which failed importing Xlib before any Fake X probe or audit.** No portability result is claimed. S07 was not retried.

S07 captured the exact error: `ModuleNotFoundError: No module named 'Xlib'` at the runner's `import Xlib` line. The runner first verified all 67 dependency file hashes under `/deps`. Its script set `PYTHONPATH=/src:/deps` only in a child-process environment, but imported Xlib in the current runner interpreter before launching those children. It never added `/deps` to that interpreter's `sys.path`. A fresh attempt can test that concrete fix; this does not revise S07.

The dedicated session started, the pinned image was pulled, and the isolated no-network container was created. The exact container, image, and session cleanup are confirmed. Before removal, the only file in the unique storage directory was `storage.vhdx` (203,423,744 bytes, SHA-256 `041cfb7892dea6d8a4961a49286dc9a839bcd15d84152ad76109d9d2d37aad51`). That exact file and then its empty parent directory were removed and verified absent. No global WSLc inventory or Docker was used.

S06 remains its own HOLD: it lacked stderr capture, so its exact runner failure was not observed. S07 establishes no real X/OS behavior, physical release, cancellation, recovery, application effect, MAP01, or live-control efficacy.
