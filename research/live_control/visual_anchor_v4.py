"""Raw matching first; trimmed fallback only for appearance-loss, not ambiguity."""
from visual_anchor_v2 import VisualAnchor as Raw
from visual_anchor_v3 import VisualAnchor as Trimmed

class VisualAnchor(Raw):
    def locate(self,image,observation_id,frame_id,allow_source=False):
        raw=super().locate(image,observation_id,frame_id,allow_source)
        if raw['status']!='lost':return dict(raw,error_method='raw')
        trimmed=Trimmed.locate(self,image,observation_id,frame_id,allow_source)
        return dict(trimmed,error_method='trimmed_fallback',raw_error=raw.get('error'))
