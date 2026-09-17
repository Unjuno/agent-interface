import base64,hashlib,pathlib,sys
parts=sorted(pathlib.Path(__file__).parent.glob("evidence.part*.b64"))
raw=base64.b64decode("".join(p.read_text().strip() for p in parts))
expected="697b7501a19dba52ffb5ec098037f95b7906229f5c1ec2c39e38f653b81d03d2"
got=hashlib.sha256(raw).hexdigest()
if got!=expected: raise SystemExit(f"archive sha mismatch {got} != {expected}")
out=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else pathlib.Path("critical_event_producer_fifo2_seqkey_v1_evidence.tar.xz")
if out.exists(): raise SystemExit(f"refusing existing output: {out}")
out.write_bytes(raw); print(f"{out} {len(raw)} bytes sha256={got}")
