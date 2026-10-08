"""Shared comparison-caller capture state; no input or freshness authority.

Only accept the exact image selected into a public presentation. Failed/omitted
presentation clears the previous candidate before validation. This proves local
response inclusion/identity, not model ingestion, redraw or task completion.
"""
import base64
from copy import deepcopy
import hashlib

class DeliveredCapture:
    def __init__(self):
        self._current=None

    @property
    def current(self):
        return deepcopy(self._current)

    def accept(self, report, shown):
        self._current=None
        try:
            if not isinstance(report,dict) or not isinstance(shown,dict):return None
            if shown.get('image_status')!='image':return None
            image=shown.get('image');ref=shown.get('image_reference')
            if not isinstance(image,dict) or not isinstance(ref,dict):return None
            if image.get('type')!='image' or image.get('mimeType')!='image/png':return None
            keys=[key for key in ('observation_id','post_dispatch_observation_id','execution_observation_index') if key in ref]
            if len(keys)!=1:return None
            key=keys[0]
            if report.get('schema')=='agent-interface/runtime-observation-v1':
                if key!='observation_id' or report.get('status')!='returned' or report.get('error') is not None:return None
                if not isinstance(ref[key],str) or not ref[key] or ref[key]!=report.get('observation_id'):return None
                native=report.get('observation')
            elif report.get('schema')=='agent-interface/runtime-dispatch-result-v1':
                post=report.get('post_dispatch_inspection',{})
                if not isinstance(post,dict) or post.get('error') is not None:return None
                if key=='post_dispatch_observation_id':
                    later=post.get('observation_report',{})
                    if post.get('status')!='needs_review' or later.get('status')!='returned' or later.get('error') is not None:return None
                    if not isinstance(ref[key],str) or not ref[key] or ref[key]!=later.get('observation_id'):return None
                    native=later.get('observation')
                elif key=='execution_observation_index':
                    index=ref[key];observations=report['result']['execution']['observations']
                    if type(index) is not int or not 0<=index<len(observations):return None
                    native=observations[index]
                else:return None
            else:return None
            artifact=native['artifact']
            if ref.get('path')!=artifact['path'] or ref.get('sha256')!=artifact['sha256']:return None
            stamp=native.get('capture_started_ns')
            if type(stamp) is not int or stamp<0 or type(ref.get('capture_ns')) is not int or ref['capture_ns']!=stamp:return None
            data=base64.b64decode(image['data'],validate=True)
            if not data.startswith(b'\x89PNG\r\n\x1a\n') or hashlib.sha256(data).hexdigest()!=artifact['sha256']:return None
            self._current=deepcopy(native)
        except (KeyError,TypeError,ValueError,AttributeError):
            return None
        return self.current
