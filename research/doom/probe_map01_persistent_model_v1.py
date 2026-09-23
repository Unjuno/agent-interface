"""Two real-image calls comparing a cold Luna session with its resumed turn."""
import argparse,json,subprocess,sys
from pathlib import Path

HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1]
PY=Path("/mnt/c/Users/junny/AppData/Local/Programs/Python/Python312/python.exe")
NODE=r"C:\Program Files\nodejs\node.exe";CLI=r"C:\Users\junny\AppData\Roaming\npm\node_modules\@openai\codex\bin\codex.js"
def win(p):return subprocess.run(["wslpath","-w",str(Path(p).resolve())],capture_output=True,text=True,check=True).stdout.strip()
def parsed(root):
 rows=[json.loads(x) for x in (root/"events.jsonl").read_text().splitlines()]
 msg=[r["item"]["text"] for r in rows if r.get("type")=="item.completed" and r.get("item",{}).get("type")=="agent_message"]
 turn=[r for r in rows if r.get("type")=="turn.completed"][-1];thread=[r["thread_id"] for r in rows if r.get("type")=="thread.started"][-1]
 return {"thread_id":thread,"action":json.loads(msg[-1]),"usage":turn["usage"]}
ap=argparse.ArgumentParser();ap.add_argument("--out",type=Path,required=True);args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=False)
images=[REPO/"research/doom/results/map01-overlap-temporal-luna-01/decision-0/temporal-sheet.png",
        REPO/"research/doom/results/map01-overlap-temporal-luna-01/decision-1/temporal-sheet.png"]
session="-";results=[]
for i,image in enumerate(images):
 root=args.out/f"call-{i}";prompt=args.out/f"prompt-{i}.txt";prompt.write_text("Select the next bounded MAP01 action from the temporal sheet.\n")
 cmd=[str(PY),win(HERE/"map01_persistent_model_runner_v1.py"),NODE,CLI,win(prompt),win(REPO),win(root),win(image),
      win(HERE/"map01_action_responder_v3.txt"),win(HERE/"map01_action_schema_v1.json"),session]
 c=subprocess.run(cmd,capture_output=True,timeout=90);(args.out/f"stdout-{i}.txt").write_bytes(c.stdout);(args.out/f"stderr-{i}.txt").write_bytes(c.stderr)
 if c.returncode:raise RuntimeError(f"call {i} failed; no retry")
 row=parsed(root);results.append(row);session=row["thread_id"]
report={"passed":results[0]["thread_id"]==results[1]["thread_id"],"calls":results,
 "same_model_session":results[0]["thread_id"]==results[1]["thread_id"],
 "claim":"two-call real DOOM image persistence mechanics; no gameplay efficacy claim"}
(args.out/"report.json").write_text(json.dumps(report,indent=2)+"\n");print(json.dumps(report,indent=2))
if not report["passed"]:raise SystemExit(1)
