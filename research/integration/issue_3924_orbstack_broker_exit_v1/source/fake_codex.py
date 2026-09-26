#!/usr/bin/env python3
import json,os,sys,time
with open(os.environ["FAKE_LOG"],"a") as f: f.write(json.dumps(sys.argv[1:])+"\n")
mode=os.environ.get("FAKE_MODE","exit0")
if mode=="sleep": time.sleep(2)
sys.stdout.write('{"fake":true}\n')
sys.exit(7 if mode=="exit7" else 0)
