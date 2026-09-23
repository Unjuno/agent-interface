"""Real MAP01 probe for bounded no-input dynamic observation."""
import argparse,json,queue,subprocess,sys,threading,time
from pathlib import Path

HERE=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument("--out",type=Path,required=True)
args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=False);runtime=args.out/"runtime"
p=subprocess.Popen([sys.executable,str(HERE/"session_map01_v4.py"),"--out",str(runtime),
    "--seed","990609","--timeout-seconds","600"],stdin=subprocess.PIPE,stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,text=True,bufsize=1)
q=queue.Queue();events=[]
def reader():
    for line in p.stdout:
        row=json.loads(line);events.append(row);q.put(row)
threading.Thread(target=reader,daemon=True).start()
def wait(test,timeout=30):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        row=q.get(timeout=end-time.monotonic())
        if test(row):return row
    raise TimeoutError()
wait(lambda r:r["event"]=="ready");initial=wait(lambda r:r["event"]=="observation")
started=time.perf_counter_ns();p.stdin.write(json.dumps({"op":"submit","id":"coast",
    "expected_sequence":initial["sequence"],"valid_until_ns":started+10_000_000_000,
    "steps":[{"op":"coast","duration_ms":2000,"sample_ms":250}]})+"\n");p.stdin.flush()
wait(lambda r:r["event"]=="accepted");terminal=wait(lambda r:r["event"]=="terminal")
p.stdin.write('{"op":"finish"}\n');p.stdin.flush();score=wait(lambda r:r["event"]=="post_control_score")
p.wait(timeout=20);(args.out/"stderr.txt").write_text(p.stderr.read())
coast=next(r for r in events if r["event"]=="coast_result")
report={"passed":terminal["status"]=="completed" and terminal["release"]["verified"]
        and coast["input_admissions"]==0 and coast["elapsed_ms"]>=2000
        and score["player_dead"] is False,
        "coast":coast,"terminal":terminal,"score":score,
        "input_admissions":sum(r["event"]=="input_admission" for r in events),
        "claim":"real continuously advancing MAP01 no-input observation operation"}
(args.out/"report.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report,indent=2));raise SystemExit(0 if report["passed"] else 1)
