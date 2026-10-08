"""Explicit fixture capture bounds, validated before any input or capture call."""
def region_for(request):
    if not isinstance(request, dict):
        raise ValueError('explicit request object required')
    region = request.get('capture_region', [0, 0, 1280, 800])
    if (type(region) is not list or len(region) != 4
            or any(type(v) is not int for v in region)):
        raise ValueError('four integer screen coordinates required')
    x, y, width, height = region
    if not (0 <= x < 1280 and 0 <= y < 800 and width > 0 and height > 0
            and x + width <= 1280 and y + height <= 800):
        raise ValueError('capture outside explicit fixture screen')
    return list(region)
