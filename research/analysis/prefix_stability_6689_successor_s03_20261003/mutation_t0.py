import copy,json,subprocess,sys,tempfile
fixture,candidate,auditor=sys.argv[1:]
baseline=json.loads(subprocess.check_output([sys.executable,candidate,fixture],text=True))
mutations={}
x=copy.deepcopy(baseline); x["rows"][0]["pending_obligations"]=[]; mutations["remove_pending_obligation"]=x
x=copy.deepcopy(baseline); x["rows"][1]["mandatory_count"]=99; mutations["mix_metric_into_counts"]=x
x=copy.deepcopy(baseline); x["rows"].pop(); mutations["drop_row"]=x
x=copy.deepcopy(baseline); x["rows"][0]["disposition"]="final_negative"; mutations["false_finalize"]=x
x=copy.deepcopy(baseline); x["rows"][0]["id"]="trace_relabel"; mutations["trace_relabel"]=x
results={}
with tempfile.TemporaryDirectory() as d:
 for name,data in mutations.items():
  path=d+"/"+name+".json"
  with open(path,"w") as f: json.dump(data,f)
  p=subprocess.run([sys.executable,auditor,fixture,path],text=True,capture_output=True)
  results[name]={"rejected":p.returncode!=0,"returncode":p.returncode}
print(json.dumps({"mutation_controls":results,"all_rejected":all(v["rejected"] for v in results.values())},sort_keys=True))
sys.exit(0 if all(v["rejected"] for v in results.values()) else 2)
