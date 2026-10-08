import hashlib,json,pathlib,subprocess
root=pathlib.Path.cwd(); p=root/"research/doom/results/absolute_pair_useful_effect_audit_20261005_a02"; f=json.loads((p/"FREEZE.json").read_text()); base=subprocess.check_output(["git","rev-parse","origin/main"],text=True).strip(); bad=[]
for rel,want in f["inputs"].items():
 path="research/doom/absolute_pair_59_4d74_20261004/"+rel
 try: data=subprocess.check_output(["git","show",f"{base}:{path}"])
 except subprocess.CalledProcessError: bad.append(path); continue
 if hashlib.sha256(data).hexdigest()!=want: bad.append(path)
result={"base_commit":base,"input_file_count":len(f["inputs"]),"mismatch_count":len(bad),"mismatches":bad,"result":"PASS" if not bad else "FAIL"}
(p/"BASE_ALIGNMENT.json").write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps(result))
raise SystemExit(bool(bad))
