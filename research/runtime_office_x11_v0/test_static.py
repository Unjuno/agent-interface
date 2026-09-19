import ast, unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent

def imported_modules(path):
    tree=ast.parse(path.read_text(), filename=path.name)
    out=[]
    for node in ast.walk(tree):
        if isinstance(node,ast.Import): out.extend(alias.name for alias in node.names)
        elif isinstance(node,ast.ImportFrom) and node.module: out.append(node.module)
    return out

class StaticTests(unittest.TestCase):
    def test_executor_does_not_import_scorer_or_openpyxl(self):
        imports=imported_modules(HERE/'experiment.py')
        self.assertFalse(any(name.startswith('openpyxl') for name in imports))
        self.assertFalse(any(name.startswith('score_workbook') for name in imports))
    def test_backend_does_not_read_workbook(self):
        imports=imported_modules(HERE/'office_backend.py')
        self.assertFalse(any(name.startswith('openpyxl') for name in imports))
        self.assertNotIn('.xlsx',(HERE/'office_backend.py').read_text())
    def test_sources_parse(self):
        for name in ('office_backend.py','experiment.py','score_workbook.py','run_private_calc.py'):
            ast.parse((HERE/name).read_text(), filename=name)
if __name__=='__main__': unittest.main()
