"""Bounded local saved-file effect evidence for a single owned Calc fixture."""
import hashlib,os,stat
from pair_saved_oracle import score_saved

def verify_saved(path,baseline_sha256):
    unavailable={'status':'unavailable'}
    if type(baseline_sha256) is not str or len(baseline_sha256)!=64 or any(c not in '0123456789abcdef' for c in baseline_sha256):return unavailable
    try:
        before=os.lstat(path)
        if not stat.S_ISREG(before.st_mode) or before.st_size>2_000_000:return unavailable
        flags=os.O_RDONLY|getattr(os,'O_BINARY',0)|getattr(os,'O_NOFOLLOW',0)
        fd=os.open(path,flags)
        try:
            opened=os.fstat(fd)
            if not stat.S_ISREG(opened.st_mode) or (opened.st_dev,opened.st_ino)!=(before.st_dev,before.st_ino):return unavailable
            with os.fdopen(fd,'rb',closefd=False) as f: blob=f.read(2_000_001)
            after=os.fstat(fd); current=os.lstat(path)
        finally:os.close(fd)
        identity=lambda x:(x.st_dev,x.st_ino,x.st_size,x.st_mtime_ns,x.st_ctime_ns)
        if len(blob)>2_000_000 or identity(opened)!=identity(after) or identity(after)!=identity(current) or len(blob)!=after.st_size:return unavailable
        digest=hashlib.sha256(blob).hexdigest()
        if digest==baseline_sha256 or score_saved(blob).get('pass_effect') is not True:return unavailable
        return {'status':'succeeded','sha256':digest,'bytes':len(blob)}
    except (OSError,ValueError,TypeError):return unavailable
