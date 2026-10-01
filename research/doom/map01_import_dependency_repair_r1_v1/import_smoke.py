import importlib.util
import sys

module = importlib.util.find_spec('openpyxl')
if module is None:
    raise SystemExit('OPENPYXL_MISSING')
print('OPENPYXL_IMPORT_PASS', module.origin)
