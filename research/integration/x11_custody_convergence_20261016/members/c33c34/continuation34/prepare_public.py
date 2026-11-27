import pathlib,json,hashlib,lzma,base64
P=pathlib.Path(__file__).resolve().parent
W=P.parent.parent.resolve();sha=lambda b:hashlib.sha256(b).hexdigest()
roots={'continuation33':P.parent/'x11-explicit-device-source-01a0ff2c','continuation34':P}
public=P/'public';public.mkdir(exist_ok=False)
members={};omissions=[]
for label,root in roots.items():
    for f in sorted(root.rglob('*')):
        if not f.is_file() or f.is_relative_to(public):continue
        rel=f.relative_to(root).as_posix();raw=f.read_bytes();item={'original_bytes':len(raw),'original_sha256':sha(raw)}
        if (label=='continuation33' and (f.suffix in ('.xz','.c','.h') or f.name in ('COPYING','FINAL_MANIFEST.json','seal.py'))) or (label=='continuation34' and rel.startswith('reference/')):
            omissions.append(dict(path=label+'/'+rel,**item,reason='third-party reference/source archive or historical seal; original retained locally; exact official archive/server refs in report'))
            continue
        content=raw.decode('utf-8')
        # Public projection: preserve original separately, do not claim projected hash is original.
        for token in [str(W),str(W).replace('\\','/'),str(W).replace('\\','\\\\')]:content=content.replace(token,'<WORKSPACE>')
        for token in ['<PYTHON3.12.10>','C:\\\\Users\\\\<LOCAL_USER>\\\\AppData\\\\Local\\\\Programs\\\\Python\\\\Python312\\\\python.exe']:
            content=content.replace(token,'<PYTHON3.12.10>')
        projected=content.encode();members[label+'/'+rel]=dict(item,public_bytes=len(projected),public_sha256=sha(projected),utf8=content)
packet={'version':1,'scope':'ordinary inert/source construction, no native/all-goal proof','projection':'workspace/interpreter paths replaced; original hashes refer to separately retained originals, not projected files; no private authentication included','reference_sources':'Official libXtst1.2.5/xorgproto2024.1 archives and XQuartz/xorg-server0ea9b595891f2f31915538192961f3404d9ca699. Omitted reference files must be recovered from exact refs for full source-reader replay; no historical sealed source is edited. Dependencies are exact read-only Python-Xlib0.33/six1.17.0 wheels, not copied here.','members':members,'explicit_omissions':omissions}
raw=json.dumps(packet,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode();comp=lzma.compress(raw,preset=6)
(public/'capsule.json').write_bytes(raw);(public/'capsule.json.xz').write_bytes(comp)
text=('Author34fb / FINAL-v5 — continuations33/34 data-only evidence, no production/native replay. V4 adoption/application HOLD; new access-suppression counterexample and standard explicit-device wire distinction. Original first scientific/construction/reader failures preserved.\n\n'
      +f'XZ/base64 capsule: JSON{len(raw)}B SHA256{sha(raw)}; XZ{len(comp)}B SHA256{sha(comp)}; {len(members)} projected full members, {len(omissions)} explicit original-reference omissions. Uncompressed member UTF8/public hashes recover exactly. Original/private hashes and path projection are distinguished; full reference-reader replay requires the pinned omitted primary sources/dependencies, not native execution. Actor/raw/results/source and three copied negative controls per construction are included.\n\n```base64\n'+base64.b64encode(comp).decode()+'\n```\n')
if len(text)>64000:raise RuntimeError('comment too large; do not post')
(public/'COMMENT-CAPSULE.txt').write_bytes(text.encode())
print(json.dumps({'members':len(members),'omissions':len(omissions),'json_bytes':len(raw),'json_sha256':sha(raw),'xz_bytes':len(comp),'xz_sha256':sha(comp),'comment_chars':len(text)}))
