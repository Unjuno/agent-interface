import json,sys
from pathlib import Path
from run_case import run

def main():
    root=Path(__file__).resolve().parents[1]
    schedule=json.loads((root/'schedule.json').read_text())
    outdir=Path(sys.argv[1]); outdir.mkdir(parents=True,exist_ok=True)
    rows=[]
    for spec in schedule:
        rows.append(run(spec['id'],spec['arm'],spec['display'],outdir/(spec['id']+'.json')))
    (outdir/'formal_rows.json').write_text(json.dumps(rows,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'rows':len(rows)}))
if __name__=='__main__':main()
