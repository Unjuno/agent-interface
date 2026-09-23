# Deterministic audit reconstruction only; this is not a new scientific allocation.
from pathlib import Path
import hashlib
from runner import run_formal

EXPECTED = "7f337e5ed0e13bb392985ac80f9c5b7fe6e2b2a0994e773d6454b5ab9de7182d"
OUT = Path("FORMAL_RESULT.reconstructed.json")
run_formal(str(OUT))
got = hashlib.sha256(OUT.read_bytes()).hexdigest()
assert got == EXPECTED, (got, EXPECTED)
print(got)
