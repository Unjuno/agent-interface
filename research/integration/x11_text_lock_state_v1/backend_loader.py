"""Load exact backend classes without the unused core manifest dependency."""
import ast
import hashlib
from pathlib import Path

BLOB = '9cae101a219348077668c8fc086acf8e13154afe'


def load_backend():
    path = Path(__file__).parent / 'source/backend.py'
    data = path.read_bytes()
    assert hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() == BLOB
    tree = ast.parse(data, filename=str(path))
    removed = [n for n in tree.body if isinstance(n, ast.ImportFrom) and n.module == 'runtime.core_v1.contract']
    assert len(removed) == 1
    tree.body = [n for n in tree.body if n not in removed]
    # No class/method/constant is transformed. Manifest and artifact methods are not called.
    namespace = {'__name__': 'frozen_backend_method_probe'}
    exec(compile(tree, str(path), 'exec'), namespace)
    return namespace['X11Backend']


def lock_clear(mask):
    """Research-only refusal predicate, not authority or an atomic input guard."""
    return type(mask) is int and 0 <= mask <= 65535 and (mask & 2) == 0
