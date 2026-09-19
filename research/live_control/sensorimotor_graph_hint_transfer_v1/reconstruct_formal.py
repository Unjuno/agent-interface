#!/usr/bin/env python3
from pathlib import Path
import gzip,hashlib
ROOT=Path(__file__).resolve().parent
GZ=ROOT/'formal-result.json.gz'
OUT=ROOT/'formal-result.json'
EXPECTED_GZ_SHA256='b7415cbe4dbc5b719f6d1b219eef180b3a42bf7dbdacdda442a87ecd8cad1461'
EXPECTED_RAW_SHA256='4a7b827d61e7f07da0e8d858a1a0422f41dcddc1a4b1084b7ff71ba279d9ca96'
EXPECTED_RAW_BYTES=20430
assert hashlib.sha256(GZ.read_bytes()).hexdigest()==EXPECTED_GZ_SHA256
raw=gzip.decompress(GZ.read_bytes())
assert len(raw)==EXPECTED_RAW_BYTES
assert hashlib.sha256(raw).hexdigest()==EXPECTED_RAW_SHA256
OUT.write_bytes(raw)
print({'ok':True,'bytes':len(raw),'sha256':EXPECTED_RAW_SHA256})
