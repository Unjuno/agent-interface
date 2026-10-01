import base64, datetime, hashlib, json, platform, subprocess, sys, time, zlib
def main():
    if len(sys.argv)!=4:
        raise SystemExit("expected candidate_b64 audit_b64 fixture_b64")
    cand=base64.b64decode(sys.argv[1]); audit=base64.b64decode(sys.argv[2]); fixture_bytes=base64.b64decode(sys.argv[3])
    fixture=json.loads(fixture_bytes)
    started=datetime.datetime.now(datetime.timezone.utc).isoformat()
    t=time.perf_counter()
    cp=subprocess.run([sys.executable,"-c",cand.decode("utf-8")],input=fixture_bytes,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=120)
    c_elapsed=time.perf_counter()-t
    if cp.returncode!=0:
        print(json.dumps({"status":"CANDIDATE_FAILED","candidate_exit":cp.returncode,
          "candidate_stderr":cp.stderr.decode("utf-8","replace"),"candidate_sha256":hashlib.sha256(cand).hexdigest(),
          "fixture_sha256":hashlib.sha256(fixture_bytes).hexdigest()},sort_keys=True,separators=(",",":")))
        raise SystemExit(cp.returncode or 1)
    candidate=json.loads(cp.stdout)
    audit_input=json.dumps({"fixture":fixture,"candidate":candidate},sort_keys=True,separators=(",",":")).encode()
    t=time.perf_counter()
    ap=subprocess.run([sys.executable,"-c",audit.decode("utf-8")],input=audit_input,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=120)
    a_elapsed=time.perf_counter()-t
    if ap.returncode!=0:
        print(json.dumps({"status":"AUDITOR_PROCESS_FAILED","candidate_exit":cp.returncode,"auditor_exit":ap.returncode,
          "auditor_stderr":ap.stderr.decode("utf-8","replace"),"candidate_sha256":hashlib.sha256(cand).hexdigest(),
          "audit_sha256":hashlib.sha256(audit).hexdigest(),"fixture_sha256":hashlib.sha256(fixture_bytes).hexdigest()},sort_keys=True,separators=(",",":")))
        raise SystemExit(ap.returncode or 1)
    audit_result=json.loads(ap.stdout)
    compressed=zlib.compress(cp.stdout,9)
    out={"status":audit_result.get("status"),"candidate_exit":cp.returncode,"auditor_exit":ap.returncode,
      "candidate_elapsed_s":round(c_elapsed,6),"auditor_elapsed_s":round(a_elapsed,6),"started_utc":started,
      "python":sys.version,"platform":platform.platform(),"candidate_sha256":hashlib.sha256(cand).hexdigest(),
      "audit_sha256":hashlib.sha256(audit).hexdigest(),"fixture_input_sha256":hashlib.sha256(fixture_bytes).hexdigest(),
      "candidate_stdout_sha256":hashlib.sha256(cp.stdout).hexdigest(),
      "candidate_stdout_zlib_base64":base64.b64encode(compressed).decode("ascii"),
      "auditor_stdout_sha256":hashlib.sha256(ap.stdout).hexdigest(),
      "auditor_stdout":ap.stdout.decode("utf-8"),"auditor_result":audit_result}
    print(json.dumps(out,sort_keys=True,separators=(",",":")))
if __name__=="__main__": main()
