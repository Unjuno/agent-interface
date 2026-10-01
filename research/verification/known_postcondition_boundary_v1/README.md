# Known postcondition boundary v1

Container-backed local verifier experiment for Issue #3048. It uses three evidence types, ten fixed scenarios, and three shadow policies. The verifier has no model/provider dependency and never authorizes consequential input. `audit.py` recomputes the safety decision from retained JSON and rejects pixel-only success.
