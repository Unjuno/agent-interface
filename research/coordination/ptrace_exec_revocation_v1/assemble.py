import argparse,json,pathlib
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('output'); a=ap.parse_args(); root=pathlib.Path(a.root); rows=[]
    for d in sorted(root.glob('chunk-*')):
        for c in sorted(d.iterdir()):
            if c.is_dir() and (c/'result.json').exists(): rows.append(json.loads((c/'result.json').read_text()))
    ids=[r['case_id'] for r in rows]
    if len(rows)!=12 or len(set(ids))!=12: raise SystemExit(f'expected 12 unique rows, got {len(rows)}/{len(set(ids))}')
    pathlib.Path(a.output).write_text(json.dumps({'allocation':'ptrace-exec-revocation-20260917-a1','formal_reruns':0,'rows':rows},sort_keys=True,indent=2)+'\n')
if __name__=='__main__': main()
