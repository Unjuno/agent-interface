import copy,json,subprocess,sys,tempfile
fixture,candidate,auditor=sys.argv[1:]
base=json.loads(subprocess.check_output([sys.executable,candidate,fixture],text=True))
mutations={}
x=copy.deepcopy(base); x["rows"].pop(); mutations["drop_row"]=x
x=copy.deepcopy(base); next(r for r in x["rows"] if r["scenario"]=="r01" and r["policy"]=="triggered")["capture_ticks"].append(1); mutations["false_capture"]=x
x=copy.deepcopy(base); next(r for r in x["rows"] if r["scenario"]=="r03" and r["policy"]=="triggered")["release"]="horizon"; mutations["target_loss_continue"]=x
x=copy.deepcopy(base); next(r for r in x["rows"] if r["scenario"]=="r04" and r["policy"]=="triggered")["actions"].append({"tick":3,"input":1.0}); mutations["lease_violation"]=x
x=copy.deepcopy(base); next(r for r in x["rows"] if r["scenario"]=="r02" and r["policy"]=="triggered")["effect"]=False; mutations["false_effect"]=x
results={}
with tempfile.TemporaryDirectory() as d:
 for n,payload in mutations.items():
  path=d+"/"+n+".json"
  with open(path,"w") as f: json.dump(payload,f)
  run=subprocess.run([sys.executable,auditor,fixture,path],capture_output=True,text=True)
  results[n]={"rejected":run.returncode!=0,"returncode":run.returncode}
print(json.dumps({"all_rejected":all(x["rejected"] for x in results.values()),"controls":results},sort_keys=True))
sys.exit(0 if all(x["rejected"] for x in results.values()) else 2)
