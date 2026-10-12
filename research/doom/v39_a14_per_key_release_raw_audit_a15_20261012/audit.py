import hashlib,json,pathlib,sys
p=pathlib.Path(__file__).parent
m=json.loads((p/'SOURCE_MANIFEST.json').read_text(encoding='utf-8'))
checks=[]
def ck(name,ok,detail=''): checks.append({'name':name,'ok':bool(ok),'detail':detail})
for rel,meta in m['files'].items():
 d=(p/rel).read_bytes(); ck('sha256:'+rel,hashlib.sha256(d).hexdigest()==meta['sha256'] and len(d)==meta['bytes'])
controller=(p/'inputs/strict_controller.py').read_bytes(); blob=hashlib.sha1(f'blob {len(controller)}\0'.encode()+controller).hexdigest(); ck('strict_controller_git_blob',blob==m['strict_release_git_blob'],blob)
for mode in ['normal','optimized']:
 log=(p/f'wslc-{mode}.txt').read_text(encoding='utf-8',errors='replace'); code=(p/f'wslc-{mode}.exit').read_text().strip()
 ck('wslc_'+mode,code=='0' and 'Ran 5 tests' in log and 'OK' in log and 'FAILED' not in log,f'exit={code}')
ck('image_identity',json.loads((p/'image-inspect.json').read_text(encoding='utf-8-sig'))[0]['Id']=='sha256:16cfda0e6a1d9077709d0cbcd378562b025bb82d8243de633da2ab31d6489cb7')
inv=(p/'container-inventory-after.txt').read_text(encoding='utf-8-sig',errors='replace').splitlines(); ck('container_inventory_empty',len(inv)<=2)
ck('swap_limitation_recorded','does not support swap limit capabilities' in (p/'wslc-normal.txt').read_text(errors='replace') and 'no swap enforcement' in (p/'README.md').read_text(encoding='utf-8'))
out={'schema':'v39-a14-per-key-reaudit-a15-v1','status':'PASS' if all(x['ok'] for x in checks) else 'FAIL','passed':sum(x['ok'] for x in checks),'total':len(checks),'checks':checks,'scope':'Saved artifact integrity and WSLc replay only; historical A14 freeze deviation remains disqualifying for efficacy claims; X11 server state is not physical keyboard observation.'}
(p/'AUDIT.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8'); print(json.dumps({k:out[k] for k in ['status','passed','total']})); [print(x) for x in checks if not x['ok']]; sys.exit(0 if out['status']=='PASS' else 1)
