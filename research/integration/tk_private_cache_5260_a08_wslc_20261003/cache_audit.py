"""Independent ephemeral-cache receipt gate; never imports cache producer."""
import re

def cache_errors(row):
    try:
        cache=row['cache'];path=cache['path']
        values=[cache['created_ns'],row['app_start_ns'],row['app_end_ns'],
                cache['cleanup_started_ns'],cache['cleanup_finished_ns']]
        if (not isinstance(path,str) or not re.fullmatch(r'/tmp/5260-a08-cache-[a-z0-9_]+',path) or
                row['app']['xdg_cache_home']!=path or cache['token']!=row['token'] or
                type(cache['mode']) is not int or cache['mode']!=0o700 or
                type(cache['uid']) is not int or cache['uid']!=65534 or
                type(cache['removed']) is not bool or not cache['removed'] or
                any(type(value) is not int or value<=0 for value in values) or values!=sorted(values)):
            return ['cache_custody']
        return []
    except (KeyError,TypeError,ValueError):return ['malformed_cache']

