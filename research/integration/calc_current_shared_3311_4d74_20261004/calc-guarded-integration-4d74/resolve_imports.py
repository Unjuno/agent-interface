import ast,json,pathlib
R=pathlib.Path(__file__).resolve().parent;modules=json.loads((R/'MODULE_INVENTORY.json').read_text(encoding='utf-8'));wanted={'runtime.guarded_x11_v1.bridge'}
for path in (R/'sources').rglob('*.py'):
 rel=path.relative_to(R/'sources').as_posix();module=rel.removesuffix('/__init__.py').removesuffix('.py').replace('/','.')
 package=module if rel.endswith('/__init__.py') else module.rsplit('.',1)[0]
 tree=ast.parse(path.read_text(encoding='utf-8'))
 for node in ast.walk(tree):
  if isinstance(node,ast.Import):
   for alias in node.names:
    if alias.name in modules:wanted.add(alias.name)
  if isinstance(node,ast.ImportFrom):
   if node.level:
    bits=package.split('.');base='.'.join(bits[:len(bits)-(node.level-1)]);name=base+('.'+node.module if node.module else '')
   else:name=node.module or ''
   if name in modules:wanted.add(name)
   for alias in node.names:
    if name+'.'+alias.name in modules:wanted.add(name+'.'+alias.name)
  if isinstance(node,ast.Constant) and isinstance(node.value,str) and node.value.startswith('runtime.') and node.value in modules:wanted.add(node.value)
for name in list(wanted):
 bits=name.split('.')
 for i in range(1,len(bits)):
  parent='.'.join(bits[:i])
  if parent in modules:wanted.add(parent)
missing=[modules[n] for n in sorted(wanted) if not (R/'sources'/modules[n]['path']).exists()]
print(json.dumps(dict(missing=missing,wanted=len(wanted))))
