import ast, base64, hashlib, json, pathlib, sys
tree=ast.parse(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
values={}
for node in tree.body:
    if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in {"SOURCES","EXPECTED","EXPECTED_SIZE"}:
        values[node.targets[0].id]=ast.literal_eval(node.value)
sources,expected,sizes=(values[k] for k in ("SOURCES","EXPECTED","EXPECTED_SIZE"))
rows=[]
for name,wrapped in sources.items():
    encoded=b"".join(wrapped.encode("ascii").split())
    raw=base64.b64decode(encoded,validate=True)
    digest=hashlib.sha256(raw).hexdigest()
    if len(raw)!=sizes[name] or digest!=expected[name]:
        raise SystemExit("STOP_DECODE_PIN:"+name)
    if any(isinstance(n,ast.Assert) for n in ast.walk(ast.parse(raw.decode("utf-8")))):
        raise SystemExit("STOP_ASSERT_PRESENT:"+name)
    rows.append({"file":name,"wrapped_chars":len(wrapped),"bytes":len(raw),"sha256":digest,"pass":True})
print(json.dumps({"status":"PREFLIGHT_PASS","files":rows},sort_keys=True))
