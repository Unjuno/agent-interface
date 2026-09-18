from pathlib import Path
import base64, gzip, hashlib, json

HERE = Path(__file__).resolve().parent
EXPECTED = "d5de4ba8137264fc1f7f444825dac94327722e7e9decc9284fd868847f8658b6"
raw = gzip.decompress(base64.b64decode((HERE / "COMPACT_EVIDENCE.json.gz.b64").read_bytes()))
c = json.loads(raw)
p = c["payload"]
for row in p["pairs_rows"]:
    for fr in row["frames"]:
        h = fr.pop("scanline_sha256")
        fr["scanline_b64"] = c["scanlines"][h]
out = HERE / "FORMAL_RESULT.reconstructed.json"
out.write_text(json.dumps(p, separators=(",", ":"), sort_keys=True), encoding="utf-8")
got = hashlib.sha256(out.read_bytes()).hexdigest()
assert got == EXPECTED == c["original_sha256"], (got, EXPECTED, c["original_sha256"])
print(got)
