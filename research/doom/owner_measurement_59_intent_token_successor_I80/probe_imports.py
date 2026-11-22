"""Non-live import preparation; never invoke session/controller main."""
import importlib.util
from pathlib import Path
import sys


def load_file(name, path):
    if name in sys.modules:
        raise ValueError('refuse cached module: ' + name)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module
