import sys,json,pathlib,hashlib,argparse
repo=pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0,str(repo));sys.path.insert(0,str(repo/'research/live_control'))
from receipt_references import compact_receipt,expand_receipt
from runtime.cli_v1.receipt import receipt_view
cases={"xterm":"composed-self-use-01/submit", "calc_early":"calc-live-review-01/save", "calc_final":"calc-final-drain-01/save", "inkscape":"inkscape-batch-reference-01/move"}
parser=argparse.ArgumentParser();parser.add_argument('--out',type=pathlib.Path,required=True);args=parser.parse_args()
root=args.out;root.mkdir(parents=True,exist_ok=False)
rows=[]
for name,directory in cases.items():
    p=repo/'runtime/results'/directory/'report.json'
    full=receipt_view(str(p));compact=compact_receipt(full)
    assert expand_receipt(compact)==full
    encode=lambda value: json.dumps(value,separators=(",",":"),ensure_ascii=False).encode()
    (root/(name+".json")).write_bytes(encode(compact))
    rows.append({"case":name,"source_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"full_view_bytes":len(encode(full)),"compact_view_bytes":len(encode(compact)),"references":len(compact["event_references"]),"roundtrip_exact":True})
(root/"SUMMARY.json").write_text(json.dumps({"scope":"same retained receipts; UTF-8 JSON bytes only; no new GUI actions or measured model tokens", "cases":rows},indent=2)+"\n")
print(json.dumps(rows,indent=2))
