#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, shutil, stat, uuid
from pathlib import Path

CHUNK = 1024 * 1024

def digest(path: Path) -> tuple[int, str]:
    h=hashlib.sha256(); n=0
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(CHUNK), b''):
            n += len(chunk); h.update(chunk)
    return n,h.hexdigest()

def fsync_dir(path: Path) -> None:
    fd=os.open(path, os.O_RDONLY | getattr(os,'O_DIRECTORY',0))
    try: os.fsync(fd)
    finally: os.close(fd)

def copy_verified(src: Path, dst: Path, expected: dict) -> dict:
    try: meta=os.lstat(src)
    except FileNotFoundError as exc: raise ValueError(f'missing source: {src}') from exc
    if stat.S_ISLNK(meta.st_mode): raise ValueError(f'symlink source forbidden: {src}')
    if not stat.S_ISREG(meta.st_mode): raise ValueError(f'regular file required: {src}')
    flags=os.O_RDONLY | getattr(os,'O_NOFOLLOW',0)
    try: fd=os.open(src, flags)
    except OSError as exc: raise ValueError(f'cannot open source safely: {src}: {exc}') from exc
    h=hashlib.sha256(); total=0
    try:
        opened=os.fstat(fd)
        if not stat.S_ISREG(opened.st_mode): raise ValueError(f'regular opened file required: {src}')
        if opened.st_size != expected['bytes']:
            raise ValueError(f'size mismatch: {src}: {opened.st_size} != {expected["bytes"]}')
        with os.fdopen(fd,'rb',closefd=False) as fin, dst.open('xb') as out:
            while True:
                chunk=fin.read(CHUNK)
                if not chunk: break
                total += len(chunk); h.update(chunk); out.write(chunk)
            out.flush(); os.fsync(out.fileno())
    finally:
        os.close(fd)
    got=h.hexdigest()
    if total != expected['bytes'] or got != expected['sha256']:
        try: dst.unlink()
        except FileNotFoundError: pass
        raise ValueError(f'identity mismatch: {src}: bytes={total} sha256={got}')
    post_n,post_h=digest(dst)
    if post_n != expected['bytes'] or post_h != expected['sha256']:
        raise ValueError(f'post-copy identity mismatch: {dst}')
    return {'name':expected['name'],'bytes':post_n,'sha256':post_h}

def materialize(jar_source: Path, save_source: Path, out: Path, identities: dict) -> dict:
    jar_source=jar_source.resolve(strict=False); save_source=save_source.resolve(strict=False)
    out=out.absolute()
    if out.exists() or out.is_symlink(): raise ValueError(f'output must be absent: {out}')
    parent=out.parent
    parent.mkdir(parents=True, exist_ok=True)
    stage=parent / ('.'+out.name+'.stage-'+uuid.uuid4().hex)
    if stage.exists(): raise RuntimeError('unexpected stage collision')
    try:
        stage.mkdir(mode=0o700)
        jar=copy_verified(jar_source, stage/identities['jar']['name'], identities['jar'])
        save=copy_verified(save_source, stage/identities['save']['name'], identities['save'])
        manifest={'schema':'mindustry_asset_materialized_v1','status':'ASSETS_READY','files':{'jar':jar,'save':save}}
        mp=stage/'MANIFEST.json'
        with mp.open('x',encoding='utf-8',newline='\n') as f:
            json.dump(manifest,f,indent=2,sort_keys=True); f.write('\n'); f.flush(); os.fsync(f.fileno())
        fsync_dir(stage)
        os.replace(stage,out)
        fsync_dir(parent)
        for key in ('jar','save'):
            exp=identities[key]; n,h=digest(out/exp['name'])
            if n != exp['bytes'] or h != exp['sha256']: raise RuntimeError('published identity drift')
        published=json.loads((out/'MANIFEST.json').read_text())
        if published != manifest: raise RuntimeError('published manifest drift')
        return manifest
    except Exception:
        if stage.exists(): shutil.rmtree(stage,ignore_errors=True)
        raise

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--jar-source',type=Path,required=True)
    ap.add_argument('--save-source',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--fixture',type=Path,required=True)
    ap.add_argument('--identity-set',choices=('production','test'),default='production')
    a=ap.parse_args(); f=json.loads(a.fixture.read_text())
    print(json.dumps(materialize(a.jar_source,a.save_source,a.out,f[a.identity_set]),sort_keys=True))
if __name__=='__main__': main()
