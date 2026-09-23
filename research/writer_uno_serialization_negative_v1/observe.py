#!/usr/bin/python3
from __future__ import annotations
import argparse,json
from uno_common import document
ap=argparse.ArgumentParser(); ap.add_argument('--pipe',required=True); ap.add_argument('--url',required=True); a=ap.parse_args(); c=document(a.pipe,a.url)
print(json.dumps({'url':str(c.URL),'uid':str(c.RuntimeUID),'text':str(c.Text.String),'controllers_locked':bool(c.hasControllersLocked())},ensure_ascii=True))
