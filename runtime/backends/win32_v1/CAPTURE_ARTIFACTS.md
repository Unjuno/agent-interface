# Optional Win32 capture PNGs

`backend.configure_capture_artifacts(directory)` enables PNG artifacts for later captures. `observe_in_session(..., capture_directory=directory)` uses that same hook. Capture saves the exact current cropped raw pixels once; it does not acquire a second frame or change focus, input, recovery or authority. Without configuration, the original metadata-only return shape remains.

An enabled capture records target/frame/region and same-process monotonic acquisition brackets plus artifact path/size/PNG hash/raw hash. Equal pixels may have distinct artifact paths. Writer failure keeps original capture metadata and `artifact_error`, without retry or replacement capture. File close does not establish fsync, redraw or task completion; a blocked native call or filesystem write is not given a hard deadline by this connection.

The existing capture contract produces top-down32-bit BI_RGB. PNG retains RGB channels and ignores the DIB's fourth byte. The writer uses only stdlib struct/zlib and refuses malformed buffers, boolean/noninteger dimensions, dimensions above8192 or more than16,777,216 pixels.

Local validation: `python -m unittest runtime.backends.win32_v1.test_capture_artifacts` runs six pure methods with inert capture endpoints. Separate full-production observe/review/receipt composition accepted the saved PNG and refused incorrect raw/PNG links. Independent Pillow decoding matched304 pixels from four already consumed owned-memory native D02 captures; D02 was not rerun. Initial missing-feature failures and an initial checker-key error are retained.

Complete56-image original construction evidence is in Issue57 comments5973072220/5973072439/5973072684/5973072955. Joined JSON SHA256860d01a2d047882b40d2065443c72b08aefc79954a8c4ff25016b939fd52d90d; gzip SHA2566a8b14ae0ecf0f6ea3f696f2546f7012dab8ecea63919a82ed3d6e149ee513fd. Actual full public restoration passed before source publication. The later portable-test adaptation is distinct ordinary product validation, not additional scientific cases.

No fresh real HWND/PrintWindow/screen/MCP delivery, model presentation, input release, task success or performance result is claimed here. This connection adds image serialization and recorded identity; existing native capture behavior and limitations remain.
