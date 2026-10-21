import ast, hashlib, json, pathlib, shutil
P=pathlib.Path(__file__).resolve().parent
path='runtime/backends/x11_v1/backend.py'
for arm in ('candidate','wrong_index'):
    root=P/'sources'/arm
    shutil.copytree(root,P/'sources'/(arm+'_indent_first'))
    file=root/path
    source=file.read_text(encoding='utf8')
    begin=source.index('   def _physical_buttons_down(')
    end=source.index('    def release_all(',begin)
    old=source[begin:end]
    fixed=''.join(' '+line if line.strip() else line for line in old.splitlines(keepends=True))
    source=source[:begin]+fixed+source[end:]
    ast.parse(source)
    file.write_bytes(source.encode())
manifest={arm:{f.relative_to(P/'sources'/arm).as_posix():{'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in sorted((P/'sources'/arm).rglob('*')) if f.is_file()} for arm in ('baseline','candidate','wrong_index','candidate_indent_first','wrong_index_indent_first')}
(P/'SOURCE_MANIFEST_REPAIRED.json').write_bytes((json.dumps(manifest,indent=2)+'\n').encode())
print('Retained initial images; fixed construction indentation only; AST parsed.')
