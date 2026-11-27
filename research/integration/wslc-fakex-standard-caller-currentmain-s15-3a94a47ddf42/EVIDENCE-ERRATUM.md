# S15 evidence correction

`run/fake-x-raw-manifest.json` is retained exactly as generated, but is invalid JSON because the runner appended a literal escaped newline. The 24 raw records themselves are unchanged. An independent local audit reconstructed `fake-x-raw-manifest-corrected.json` from those files, verified every byte count and SHA-256, and matched the manifest payload digest in `result.json`. No WSLc or test rerun occurred.
