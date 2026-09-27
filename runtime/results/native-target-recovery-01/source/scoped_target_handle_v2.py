"""Target-handle v2 refuses visually flat source regions before minting."""
from PIL import ImageStat

from scoped_target_handle_v1 import TargetHandleStore as Previous


class FlatTargetRefused(ValueError):
    """Source texture refused before minting a handle or dispatching input."""


class TargetHandleStore(Previous):
    def mint(self, name, coordinate_frame, box, observation, image, now_ns,
             ttl_ms=30000, freshness_ms=1000, search_radius=0,
             allowed_transformations=("window_translation",)):
        if (getattr(image, "mode", None) != "RGB" or type(box) is not list or
                len(box) != 4 or any(type(value) is not int for value in box)):
            raise ValueError("RGB image and integer region required")
        x, y, width, height = box
        if x < 0 or y < 0 or width <= 0 or height <= 0:
            raise ValueError("valid source region required")
        patch = image.crop((x, y, x + width, y + height))
        if patch.size != (width, height) or max(ImageStat.Stat(patch).stddev) < 8:
            raise FlatTargetRefused("visually flat target region refused")
        return super().mint(name, coordinate_frame, box, observation, image, now_ns,
                            ttl_ms, freshness_ms, search_radius,
                            allowed_transformations)
