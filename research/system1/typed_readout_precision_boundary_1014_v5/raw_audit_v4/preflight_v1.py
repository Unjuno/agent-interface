import ast,base64,hashlib,json,pathlib,sys
tree=ast.parse(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
wanted={"SOURCES","EXPECTED","EXPECTED_SIZE","BASELINE_REPORT_B64","BASELINE_SHA","BASELINE_SIZE","CANONICAL_SHA","CANONICAL_SIZE"}
values={}
for node in tree.body:
    if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in wanted:
        values[node.targets[0].id]=ast.literal_eval(node.value)
def dec(value):
    return base64.b64decode(b"".join(value.encode("ascii").split()),validate=True)
rows=[]
for name,wrapped in values["SOURCES"].items():
    raw=dec(wrapped); digest=hashlib.sha256(raw).hexdigest()
    if len(raw)!=values["EXPECTED_SIZE"][name] or digest!=values["EXPECTED"][name]:
        raise SystemExit("STOP_SOURCE_PIN:"+name)
    if any(isinstance(n,ast.Assert) for n in ast.walk(ast.parse(raw.decode("utf-8")))):
        raise SystemExit("STOP_ASSERT_PRESENT:"+name)
    rows.append({"file":name,"bytes":len(raw),"sha256":digest,"pass":True})
baseline=dec(values["BASELINE_REPORT_B64"])
if len(baseline)!=values["BASELINE_SIZE"] or hashlib.sha256(baseline).hexdigest()!=values["BASELINE_SHA"]:
    raise SystemExit("STOP_BASELINE_RAW_PIN")
canonical=baseline.replace(b"\r\n",b"\n")
if b"\r" in canonical or len(canonical)!=values["CANONICAL_SIZE"] or hashlib.sha256(canonical).hexdigest()!=values["CANONICAL_SHA"]:
    raise SystemExit("STOP_BASELINE_CANONICAL_PIN")
print(json.dumps({"status":"PREFLIGHT_PASS","sources":rows,"baseline_bytes":len(baseline),"baseline_sha256":hashlib.sha256(baseline).hexdigest(),"canonical_bytes":len(canonical),"canonical_sha256":hashlib.sha256(canonical).hexdigest()},sort_keys=True))
