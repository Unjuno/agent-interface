# Controlled Calc partial-entry recovery after key-down

Two separately registered, network-disabled Calc trials exercise one controlled
failure: the guarded backend sends the third digit's key-down request and a test
hook then raises before the normal key-up path. The backend reports the text
operation as failed with its effect unknown and attempts release. A separate
owner must establish a fresh visible state before any further input. Neither
trial is a model-driven caller or compiled-graph recovery test.

| Trial | Fresh-observation budget | Result |
|---|---:|---|
| `two-second-refusal` | 2 s | OCR eventually observed `731`; the guarded Enter was refused before input when the deadline expired during target capture. No Save was sent. |
| `four-second-success` | 4 s | OCR observed `731`; the new owner sent no text, then issued guarded Enter and Save. The saved FODS contains numeric A1 `731` and no formula. |

Both trials recorded the first owner's verified release and neutral X key/button
state. The successful trial also recorded distinct owner sessions, verified
releases after Enter and Save, and neutral final X state. Its independent
read-only audit re-ran Tesseract on the retained image, checked the submitted
program inventory, original deadline, release receipts and saved FODS; the
boundary audit additionally rehashed the runtime snapshot. The failed trial's
separate raw trace shows the deadline refusal and no recovery program.

These were one trial per budget, using an existing pinned image with a private
Xvfb, 1 CPU, 1 GiB memory and memory-plus-swap cap, and zero model calls. The
launcher was Docker Desktop from the shared Windows/WSL host; it was not a
managed WSLc allocation. The 4 s budget was selected after the 2 s failure.
Tesseract page segmentation mode 8 was selected after examining prior saved
images. The two trials are not a matched efficiency comparison or a statistical
estimate. A key-down request and an X server acknowledgement do not alone prove
application delivery: the fresh OCR and independently parsed saved file are
separate observations. X neutral state is not hardware-level release evidence.

The failure is intentionally injected at a known hook. It does not establish
recovery from arbitrary process death, host crash, a persistent obstruction,
arbitrary edits, or unbounded/late effects. OCR and saved-effect checks cover
one known value and layout; they do not establish a general recognizer. No
hard-real-time guarantee, model cost or broad reliability claim follows.

`two-second-refusal.zip` and `four-second-success.zip` include the registered
candidate, source snapshot manifest, images, receipts, output and seals.
Archive SHA-256 values are respectively
`ad376330ab7b853f96ebd9036ed7b5815401406f72239429aacb7ecdf9582fd1` and
`bc22951f1e486e76eb7cba5ec52e56cd6533979186a7156180bd61371c5795f9`.
They include no model protocol journals. Prior exploratory OCR and pre-key
trials are not included in these archives and are not counted as passes.

Run `python3 -B audit.py` with Tesseract installed. It checks archive and seal
hashes, frozen runtime files, the failed trial's pre-dispatch refusal, and
re-runs the successful trial's retained OCR/effect and boundary auditors. The
auditor is read-only apart from its temporary extraction directory. A local
corruption check also verified that a modified archive is rejected before
extraction. `audit-result.json` records the original audit run.

## Runtime provenance

The 383 retained runtime files exactly match the runtime files present in local
checkout revision `55c22b21f5a8465420de792c3c8a565d14bd8543`, as verified by
Git blob hashes. That checkout's full tree is also represented by draft
[PR #10587](https://github.com/Unjuno/agent-interface/pull/10587) commit
`4e4588a5d2f39b8b821dae15cc05f39eb9ec0198`. Relative to main at the time of
the experiment, the snapshot differs in `runtime/guarded_x11_v1/target_queries.py`
and its corresponding test. It is therefore a frozen research snapshot, not
an unqualified test of then-current main. The 383-file manifest remains the
byte-level authority; it is not a complete checkout manifest.
