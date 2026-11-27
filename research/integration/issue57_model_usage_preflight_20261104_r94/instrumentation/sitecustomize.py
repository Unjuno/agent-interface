import json, os, shutil, stat
from pathlib import Path
from runtime.guarded_x11_v1 import calc_effect_v1, calc_task_artifact_v1
_original = calc_effect_v1._read_regular
def _instrumented(path, *, max_bytes):
    try:
        return _original(path, max_bytes=max_bytes)
    except Exception as exc:
        p = Path(path)
        dest = Path(os.environ['AGENT_INTERFACE_CALC_READ_DIAGNOSTIC']).resolve()
        dest.mkdir(parents=True, exist_ok=False)
        facts = {'path': str(p), 'exists': p.exists(), 'exception_type': type(exc).__name__, 'exception': str(exc), 'max_bytes': max_bytes}
        try:
            info = p.lstat()
            facts['lstat'] = {'mode': info.st_mode, 'is_regular': stat.S_ISREG(info.st_mode), 'size': info.st_size, 'dev': info.st_dev, 'ino': info.st_ino, 'mtime_ns': info.st_mtime_ns, 'ctime_ns': info.st_ctime_ns}
        except Exception as stat_exc:
            facts['stat_error'] = {'type': type(stat_exc).__name__, 'message': str(stat_exc)}
        facts['parent_names'] = [x.name for x in p.parent.iterdir()] if p.parent.exists() else None
        (dest/'read-failure.json').write_text(json.dumps(facts, indent=2)+'\n', encoding='utf-8')
        if p.parent.exists():
            shutil.copytree(p.parent, dest/'call-artifacts', dirs_exist_ok=True)
        raise
calc_effect_v1._read_regular = _instrumented
calc_task_artifact_v1._read_regular = _instrumented
