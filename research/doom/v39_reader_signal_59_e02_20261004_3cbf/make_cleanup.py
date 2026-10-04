"""Mechanical extraction of already-reviewed E01 cleanup (no native run)."""
import ast
import hashlib
import pathlib
root=pathlib.Path(__file__).parent
source=(root/'source/e01-probe.py.txt').read_bytes()
assert hashlib.sha256(source).hexdigest()=='3db505015d7ea917e66447f9057dce2504a6d2a746abaa6b033b595ea2dc5982'
tree=ast.parse(source.decode())
node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='cleanup')
(root/'cleanup.py').write_text(ast.unparse(node)+'\n')
