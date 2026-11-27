"""Resolve the newest image explicitly referenced by a received batch.

Local run directory and runtime path are explicit; never infer image indices.
"""
import argparse,hashlib,json
from pathlib import Path


def select_image(batch,run_directory):
    root=Path(run_directory).resolve(strict=True)
    if not isinstance(batch,dict) or not isinstance(batch.get('records'),list):raise ValueError('record batch required')
    candidates=[]
    for record in batch['records']:
        if not isinstance(record,dict):raise ValueError('invalid record')
        if record.get('event')=='observation':obs=record
        elif record.get('event')=='terminal':obs=record.get('review',{}).get('observation')
        else:continue
        if obs is None:continue
        if not isinstance(obs,dict) or type(obs.get('sequence'))is not int or obs['sequence']<1:raise ValueError('invalid observation sequence')
        candidates.append(obs)
    if not candidates:return dict(status='no_observation',authority='none')
    newest=max(obs['sequence'] for obs in candidates)
    selected=[obs for obs in candidates if obs['sequence']==newest]
    references=[]
    for obs in selected:
        if not isinstance(obs.get('image'),str) or not obs['image']:raise ValueError('newest observation lacks image')
        if type(obs.get('capture_ns'))is not int or obs['capture_ns']<1:raise ValueError('newest observation lacks capture time')
        path=Path(obs['image'])
        if not path.is_absolute():raise ValueError('absolute runtime image reference required')
        path=path.resolve(strict=True)
        if not path.is_relative_to(root) or not path.is_file():raise ValueError('image outside run directory')
        if path.suffix.lower()!='.png':raise ValueError('PNG reference required')
        references.append((path,obs['capture_ns']))
    if len(set(references))!=1:raise ValueError('conflicting newest observation references')
    path,captured=references[0]
    return dict(status='image',sequence=newest,capture_ns=captured,path=str(path),relative_path=str(path.relative_to(root)),
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(),authority='none',freshness='historical referenced capture; no new observation')
