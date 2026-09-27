# Formal allocation STOP — Issue #4507

Disposition: STOP_OUTPUT_DIRECTORY_CONTRACT. The frozen host orchestrator invoked the training container once (exit 1), then did not start the independent auditor. Retry count: 0. No optimizer update or held-out evaluation occurred; this is not a scientific PASS/FAIL/HOLD.

The orchestrator first wrote FORMAL_INVOCATION.json into the writable output mount, then launched runner.py. The frozen runner requires the output mount to be empty at startup and exited with dedicated_empty_output_directory_required. The allocation is consumed; do not retry or edit this allocation's frozen sources. The benign PyTorch NumPy warning is retained in exact stderr bytes and is separate from the fatal output-directory guard.

The lossless capture in FORMAL_STOP_BUNDLE.json stores each original output file as base64 with byte count and SHA-256. Training stdout is empty (SHA-256 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855). Training stderr is 322 bytes (SHA-256 20850f330e515e6b5e9d70af6ffc1d646529f7655a2bbd6832a045dd32834951). The image ID matched the freeze: sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e.

A future allocation, if justified, must have a distinct issue/allocation identity and fresh seed block, with invocation metadata kept outside the empty runner output mount (or a separately frozen output contract). It must retain the original #4507 CPU-only latency interpretation; no GPU substitution.