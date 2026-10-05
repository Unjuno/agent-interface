# A04 construction record

- A01/A02/A03 each stopped at a frozen exact-main gate with candidate/auditor
  0/0. Their frozen inputs remain unmodified.
- A09's recorded candidate/auditor hashes disagree with current-main source
  bytes. A04 freshly pins the actual current-main source hashes and explicitly
  disclaims continuity with the A09 historical freeze.
- A09's Python image is unavailable locally. The cached Python 3.14.8
  Linux/arm64 image `c3e521...ce40151` passed path-local A02 mount preflight;
  no image pull was used.
- A04 construction tests and own mount preflight precede freeze. Formal
  invocations remain 0/0 until `execute_formal.py` reaches the fresh-main gate.
