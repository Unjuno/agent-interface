import pathlib,json,hashlib,xml.etree.ElementTree as E
R=pathlib.Path(__file__).resolve().parent;O=R/'output';raw=json.loads((O/'raw.json').read_text(encoding='utf-8-sig'));freeze=json.loads((R/'FREEZE.json').read_text(encoding='utf-8-sig'));errors=[]
for name,digest in freeze['files'].items():
    if hashlib.sha256((R/name).read_bytes()).hexdigest()!=digest:errors.append('source:'+name)
if raw['errors'] or raw['parent_exit']!=0:errors.append('producer_or_cleanup')
rows={r['case']:r for r in raw['rows']};decision='HOLD_OPERATION_NOT_RECORDED'
if set(rows)!= {'single_visible','hidden_attached'}:errors.append('coverage')
elif all(r['disposition']=='OBSERVED' for r in rows.values()):
    ns={'t':'urn:oasis:names:tc:opendocument:xmlns:table:1.0','x':'urn:oasis:names:tc:opendocument:xmlns:text:1.0'}
    for case,row in rows.items():
        events={e['stage']:e for e in row['events']};before=events['before_undo'];after=events['after_undo'];expected_b='PROTECTED' if case=='single_visible' else ''
        if (before['A1'],before['B1'])!=('OWNED','PROTECTED'):errors.append('before:'+case)
        if (after['A1'],after['B1'])!=('',expected_b):errors.append('footprint:'+case)
        b=(O/(case+'.fods')).read_bytes()
        if hashlib.sha256(b).hexdigest()!=row['saved_sha256']:errors.append('saved_hash:'+case)
        root=E.fromstring(b);table=root.find('.//t:table',ns);first=table.find('t:table-row',ns);cells=first.findall('t:table-cell',ns);expanded=[]
        for cell in cells:
            count=int(cell.get('{'+ns['t']+'}number-columns-repeated','1'));value=''.join(cell.itertext()).strip();expanded.extend([value]*min(count,2-len(expanded)))
            if len(expanded)>=2:break
        if expanded[:2]!=['',expected_b]:errors.append('saved_effect:'+case+str(expanded[:2]))
    a={e['stage']:e for e in rows['single_visible']['events']}['before_undo'];b={e['stage']:e for e in rows['hidden_attached']['events']}['before_undo']
    if a['titles']!=b['titles'] or a['undo_possible']!=b['undo_possible'] or a['locked']!=b['locked']:errors.append('visible_metadata_contrast_absent')
    decision='SUPPORT_VISIBLE_HISTORY_INSUFFICIENT_SCOPED' if not errors else 'FAIL_OR_HOLD'
print(json.dumps({'decision':decision,'errors':errors,'scope':'independent raw timeline + saved FODS cells, authored hidden context only; no model judgment or independent-writer proof'},indent=2));raise SystemExit(bool(errors))
