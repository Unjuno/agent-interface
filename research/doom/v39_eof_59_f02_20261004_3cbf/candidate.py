"""Research successor of exact E02 reader/wait; not full controller adoption."""
import sys
import ast
import hashlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'v39_os_pipe_59_f01_20261004_3cbf'))
from probe import factory as historical_factory


def factory(source):
    if hashlib.sha256(source).hexdigest() != 'dca770e5e0c532b301b12032c9532bd5fae602947caff4fff21bde60634a57f1':
        raise ValueError('exact E02 candidate source required')
    tree = ast.parse(source)
    main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
    reader = next(node for node in main.body if isinstance(node, ast.FunctionDef) and node.name == 'reader')
    protected = reader.body[0]
    if not isinstance(protected, ast.Try) or len(protected.body) != 1 or not isinstance(protected.body[0], ast.For):
        raise ValueError('unexpected reader structure')
    protected.body.extend(ast.parse('raise EOFError("session stdout closed before another expected event")').body)
    create = historical_factory(ast.unparse(ast.fix_missing_locations(tree)).encode())

    def create_persistent(process, incoming):
        reader, wait, events = create(process, incoming)
        closure = dict(zip(reader.__code__.co_freevars,
                           (cell.cell_contents for cell in reader.__closure__)))
        marker_type = closure['_SessionReaderFailure']
        failure = None

        def wait_persistent(*args, **kwargs):
            nonlocal failure
            if failure is not None:
                failure_type, arguments, cause = failure
                raise failure_type(*arguments) from cause
            try:
                return wait(*args, **kwargs)
            except RuntimeError as error:
                if type(error) is marker_type:
                    failure = (type(error), error.args, error.__cause__)
                raise

        return reader, wait_persistent, events

    return create_persistent
