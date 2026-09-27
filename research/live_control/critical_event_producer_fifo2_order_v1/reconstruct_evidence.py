import base64,hashlib,pathlib,sys
parts=[pathlib.Path(__file__).with_name(f"evidence.part{i:02d}.b64") for i in range(1,4)]
raw=base64.b64decode("".join(p.read_text().strip() for p in parts))
expected="352f79424bb241e67dd921a0049ece008268c59e87a469c3eec8b8dc7331c57e"
got=hashlib.sha256(raw).hexdigest()
if got!=expected: raise SystemExit(f"archive sha mismatch {got} != {expected}")
out=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else pathlib.Path("critical_event_producer_fifo2_order_v1_evidence.tar.xz")
if out.exists(): raise SystemExit(f"refusing existing output: {out}")
out.write_bytes(raw); print(f"{out} {len(raw)} bytes sha256={got}")
