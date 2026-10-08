# Packaging failure 01

- Stage: post-formal lossless evidence unpack validation.
- Scientific allocation impact: none; formal45 already complete and unchanged.
- Failure: `base64.b64decode(txt, validate=True)` rejected the intentionally newline-terminated Base64 part files.
- Correction: strip ASCII surrounding whitespace before strict Base64 decode while continuing to verify the exact text-file SHA256/size first. Archive bytes, part files, PACK.json, formal evidence and scientific source are unchanged.
