import importlib.abc
import sys

class _RejectPIL(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "PIL" or fullname.startswith("PIL."):
            raise ModuleNotFoundError("PIL blocked by frozen A05 import probe", name=fullname)
        return None

sys.meta_path.insert(0, _RejectPIL())
