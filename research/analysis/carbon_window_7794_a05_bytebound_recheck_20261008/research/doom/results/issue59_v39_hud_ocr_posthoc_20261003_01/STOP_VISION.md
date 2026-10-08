# STOP — Apple Vision OCR availability

- **Issue context:** #59 asks for independently useful task feedback under
  frontier-model latency. This was a proposed post-hoc image-reader probe only;
  it was not the separately gated live experiment.
- **Intended test:** run Apple's Vision text recognizer on the same 14 retained
  health-transition HUD crops, without changing game, model, or input state.
- **First command:** `swift --version`
- **Observed result:** `You have not agreed to the Xcode license agreements.
  Please run 'sudo xcodebuild -license' from within a Terminal window to review
  and agree to this license.`
- **Safe alternative check:** `import Vision` failed with
  `ModuleNotFoundError` in both the bundled Python 3.12 runtime and
  `/opt/homebrew/bin/python3`.
- **Disposition:** `STOP_MACOS_VISION_RUNTIME_UNAVAILABLE`; zero images were
  processed. No license acceptance, privileged action, dependency install, or
  retry was attempted. Linux OrbStack cannot provide the macOS Vision
  framework, and its shared image store remains unhealthy.
- **What remains:** this says nothing about Vision OCR accuracy. The Tesseract
  post-hoc result remains the only executed generic OCR probe in this package.
