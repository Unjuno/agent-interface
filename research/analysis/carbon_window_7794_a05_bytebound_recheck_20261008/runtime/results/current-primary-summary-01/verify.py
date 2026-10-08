"""Read-only retained primary evidence checks; no GUI or input."""
import base64, hashlib, io, json, pathlib, tarfile, zipfile
import xml.etree.ElementTree as ET
ROOT = pathlib.Path(__file__).resolve().parent
def require(condition, message):
    if not condition: raise ValueError(message)
def main():
    manifest = json.loads((ROOT / "manifest.json").read_text())
    with tarfile.open(ROOT / "raw.tar.gz") as archive:
        files = {m.name: archive.extractfile(m).read() for m in archive.getmembers() if m.isfile()}
    require(set(files) == set(manifest), "member set")
    for name, data in files.items():
        require(len(data) == manifest[name]["bytes"] and hashlib.sha256(data).hexdigest() == manifest[name]["sha256"], name)
    def read(name): return json.loads(files[name])
    rows = []
    for prefix, tools, reviewed in [
        ("entry", ["observe", "dispatch", "dispatch", "close"], [1,2,3]),
        ("calc", ["observe", "dispatch", "dispatch", "inspect_target", "review_target", "dispatch", "inspect_target", "close"], [1,2,3,5,6,7])]:
        actual = [read(f"{prefix}/host/request-{i}.json")["tool"] for i in range(1,len(tools)+1)]
        require(actual == ["interface_"+x for x in tools], "call order")
        summary_bytes = 0
        for i, tool in enumerate(tools,1):
            reply_bytes = files[f"{prefix}/host/reply-{i}.json"]
            reply = json.loads(reply_bytes)
            require(reply["status"] == "returned", "transport outcome")
            contents = reply["result"]["content"]
            view = json.loads(next(c["text"] for c in contents if c["type"] == "text"))
            if tool == "dispatch":
                require(view["receipt"]["schema"] == "agent-interface/receipt-view-dispatch-summary-v1", "summary")
                require(view["outcome_summary"]["execution_status"] == "completed", "execution")
                require(view["outcome_summary"]["input_release_verified"] is True, "release")
                summary_bytes += sum(len(c["text"].encode()) for c in contents if c["type"] == "text")
            if i in reviewed:
                review = read(f"{prefix}/host/review-{i}.json")
                require(review["reply_sha256"] == hashlib.sha256(reply_bytes).hexdigest(), "review binding")
                images = [hashlib.sha256(base64.b64decode(c["data"],validate=True)).hexdigest() for c in contents if c["type"] == "image"]
                require(images == [x["sha256"] for x in review["images"]] and len(images)==1, "review images")
        require(read(prefix+"/host/exit.json")["code"] == 0, "transport exit")
        require(all(c["returncode"] is not None for c in read(prefix+"/cleanup.json")), "cleanup terminal")
        require(read(prefix+"/evaluation.json")["success"] is True, "evaluation")
        rows.append({"task":prefix,"calls":len(tools),"reviewed_images":len(reviewed),"dispatch_text_bytes":summary_bytes})
    require(read("entry/effect.json") == {"saved":True,"text":"http://q_r"}, "entry effect")
    with zipfile.ZipFile(io.BytesIO(files["calc/saved.xlsx"])) as z:
        sheet = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
    ns={"s":"http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    values={c.attrib["r"]:c.find("s:v",ns).text for c in sheet.findall(".//s:c",ns) if c.find("s:v",ns) is not None}
    require(values.get("A1")=="413" and values.get("A2")=="382", "saved worksheet")
    print(json.dumps({"status":"PASS","files":len(files),"rows":rows,"scope":"retained effects and reply/review identity; not pixel interpretation, model tokens or causal speedup"}))
if __name__ == "__main__": main()
