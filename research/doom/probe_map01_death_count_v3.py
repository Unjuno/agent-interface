"""Force a visible death/restart path and test post-control DEATHCOUNT."""
import argparse,json,queue,subprocess,sys,threading,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument("--out",type=Path,required=True);args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=False)
p=subprocess.Popen([sys.executable,str(HERE/"session_map01_v5.py"),"--out",str(args.out/"runtime"),
 "--seed","990613","--timeout-seconds","120","--skill","5"],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
q=queue.Queue();events=[]
def reader():
 for line in p.stdout:
  row=json.loads(line);events.append(row);q.put(row)
threading.Thread(target=reader,daemon=True).start();latest=None
def wait(test,timeout=40):
 global latest
 end=time.monotonic()+timeout
 while time.monotonic()<end:
  row=q.get(timeout=end-time.monotonic())
  if row["event"]=="observation":latest=row
  if test(row):return row
 raise TimeoutError()
def submit(identifier,steps):
 p.stdin.write(json.dumps({"op":"submit","id":identifier,"expected_sequence":latest["sequence"],
  "valid_until_ns":time.perf_counter_ns()+20_000_000_000,"steps":steps})+"\n");p.stdin.flush()
 wait(lambda r:r["event"]=="accepted" and r.get("id")==identifier)
 return wait(lambda r:r["event"]=="terminal" and r.get("id")==identifier)
wait(lambda r:r["event"]=="ready");latest=wait(lambda r:r["event"]=="observation")
submit("enter-combat",[{"op":"hold","keys":["Up","Shift_L","space"],"duration_ms":1600},
 {"op":"hold","keys":["Right","space"],"duration_ms":500},
 {"op":"hold","keys":["Up","Shift_L","space"],"duration_ms":900},
 {"op":"hold","keys":["Right","space"],"duration_ms":750},
 {"op":"hold","keys":["Up","Shift_L","space"],"duration_ms":1300}])
for i in range(6):submit(f"exposed-{i}",[{"op":"coast","duration_ms":5000,"sample_ms":500}])
submit("restart-attempt",[{"op":"hold","keys":["space"],"duration_ms":150},{"op":"coast","duration_ms":2000,"sample_ms":500}])
p.stdin.write('{"op":"finish"}\n');p.stdin.flush();score=wait(lambda r:r["event"]=="post_control_score");p.wait(timeout=20)
(args.out/"stderr.txt").write_text(p.stderr.read());report={"score":score,"death_count_detected":score["death_count"]>0,
 "claim":"scorer calibration; scripted input, not agent gameplay"};(args.out/"report.json").write_text(json.dumps(report,indent=2)+"\n");print(json.dumps(report,indent=2))
