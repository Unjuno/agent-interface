"""Image-only controller primitives frozen for Issue #8636 T0 A01."""
from __future__ import annotations
import math

W = H = 96
CX = CY = 47.5
F_NOM = 48.0
GAIN = 0.72
ACTION_LIMIT = 0.08
STOP_TOL = 0.015
COLORS = ((255, 0, 0), (0, 255, 0), (0, 0, 255))


def read_ppm(path: str) -> tuple[int, int, bytes]:
    data = open(path, "rb").read()
    head, pixels = data.split(b"\n255\n", 1)
    parts = head.split()
    if parts[0] != b"P6":
        raise ValueError("not P6")
    width, height = int(parts[1]), int(parts[2])
    if len(pixels) != width * height * 3:
        raise ValueError("bad PPM length")
    return width, height, pixels


def detect(width: int, height: int, pixels: bytes) -> list[tuple[float, float]]:
    found = []
    for color in COLORS:
        xs, ys = [], []
        for y in range(height):
            row = y * width * 3
            for x in range(width):
                if tuple(pixels[row + x * 3:row + x * 3 + 3]) == color:
                    xs.append(x); ys.append(y)
        if len(xs) != 9:
            raise ValueError("landmark missing or ambiguous")
        found.append((sum(xs) / 9.0, sum(ys) / 9.0))
    return found


def bearing(point: tuple[float, float]) -> tuple[float, float, float]:
    x = (point[0] - CX) / F_NOM
    y = -(point[1] - CY) / F_NOM
    n = math.sqrt(x*x + y*y + 1.0)
    return (x/n, y/n, 1.0/n)


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def norm(a):
    return math.sqrt(dot(a, a))


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def scale(a, k):
    return tuple(x*k for x in a)


def sub(a, b):
    return tuple(x-y for x, y in zip(a, b))


def unit(a):
    n = norm(a)
    if n < 1e-9:
        raise ValueError("singular landmark frame")
    return scale(a, 1.0/n)


def frame(points):
    b = [bearing(p) for p in points]
    e1 = unit(b[0])
    ortho = sub(b[1], scale(e1, dot(b[1], e1)))
    if norm(ortho) < 0.08:
        raise ValueError("near-singular landmark geometry")
    e2 = unit(ortho)
    e3 = unit(cross(e1, e2))
    return (e1, e2, e3), b


def matmul(a, b):
    return tuple(tuple(sum(a[i][k]*b[k][j] for k in range(3)) for j in range(3)) for i in range(3))


def transpose(a):
    return tuple(tuple(a[j][i] for j in range(3)) for i in range(3))


def matrix_from_columns(cols):
    return tuple(tuple(cols[j][i] for j in range(3)) for i in range(3))


def rotation_error(cur_points, ref_points):
    fc, bc = frame(cur_points)
    fr, br = frame(ref_points)
    # Shape mismatch is a fail-closed cue for focal shift, target loss, or bad matches.
    angles = [math.acos(max(-1.0, min(1.0, dot(bc[i], bc[j])))) for i, j in ((0,1),(0,2),(1,2))]
    ref_angles = [math.acos(max(-1.0, min(1.0, dot(br[i], br[j])))) for i, j in ((0,1),(0,2),(1,2))]
    if max(abs(a-r) for a, r in zip(angles, ref_angles)) > 0.09:
        raise ValueError("feature shape changed")
    r = matmul(matrix_from_columns(fc), transpose(matrix_from_columns(fr)))
    # For the frozen Y(yaw) X(pitch) camera convention, extract the two
    # relative-look coordinates from the image-derived rotation matrix.
    yaw = math.atan2(-r[0][2], r[0][0])
    pitch = math.atan2(r[1][2], r[2][2])
    cosine=max(-1.0,min(1.0,(r[0][0]+r[1][1]+r[2][2]-1.0)/2.0))
    theta=math.acos(cosine)
    if theta<1e-10:
        rotvec=(0.0,0.0,0.0)
    else:
        den=2.0*math.sin(theta)
        rotvec=tuple(theta*x/den for x in (r[2][1]-r[1][2],r[0][2]-r[2][0],r[1][0]-r[0][1]))
    return yaw, pitch, angles, tuple(angles)+rotvec


def raw_features(cur_points, ref_points):
    cur=[((x-CX)/F_NOM,-(y-CY)/F_NOM) for x,y in cur_points]
    ref=[((x-CX)/F_NOM,-(y-CY)/F_NOM) for x,y in ref_points]
    return tuple(value for i in range(3) for value in (cur[i][0]-ref[i][0],cur[i][1]-ref[i][1]))


def feature_vector(arm, cur_points, ref_points):
    if arm=="raw_pixels": return raw_features(cur_points,ref_points)
    if arm=="spherical_features": return rotation_error(cur_points,ref_points)[3]
    return None


def raw_error(cur_points, ref_points):
    # Fixed first-order image Jacobian generated from the reference points;
    # solve the two-column least-squares problem with the frozen f_nom model.
    cur = [((x-CX)/F_NOM, -(y-CY)/F_NOM) for x, y in cur_points]
    ref = [((x-CX)/F_NOM, -(y-CY)/F_NOM) for x, y in ref_points]
    eps = 1e-5
    def projected(yaw, pitch):
        cy, sy = math.cos(yaw), math.sin(yaw)
        cp, sp = math.cos(pitch), math.sin(pitch)
        q = ((cy, sy*sp, sy*cp), (0.0, cp, -sp), (-sy, cy*sp, cy*cp))
        out=[]
        for x,y in ref:
            z=(x,y,1.0); cam=tuple(sum(q[k][i]*z[k] for k in range(3)) for i in range(3))
            if cam[2] <= 0.1: raise ValueError("behind camera")
            out.extend((cam[0]/cam[2],cam[1]/cam[2]))
        return out
    base=projected(0.0,0.0)
    jy=projected(eps,0.0); jp=projected(0.0,eps)
    a=[(jy[i]-base[i])/eps for i in range(6)]
    b=[(jp[i]-base[i])/eps for i in range(6)]
    d=[cur[i//2][i%2]-ref[i//2][i%2] for i in range(6)]
    aa=sum(x*x for x in a); ab=sum(x*y for x,y in zip(a,b)); bb=sum(x*x for x in b)
    ad=sum(x*y for x,y in zip(a,d)); bd=sum(x*y for x,y in zip(b,d))
    det=aa*bb-ab*ab
    if det < 1e-10: raise ValueError("ill-conditioned raw Jacobian")
    return ((ad*bb-bd*ab)/det,(bd*aa-ad*ab)/det)


def choose_action(arm, cur_points, ref_points, frame_meta):
    if frame_meta["width"] != W or frame_meta["height"] != H:
        raise ValueError("viewport dimensions changed")
    if frame_meta["target_generation"] != frame_meta["viewport_generation"]:
        raise ValueError("stale target generation")
    # Shared correspondence/geometry integrity gate; it does not steer either arm.
    _, cb = frame(cur_points); _, rb = frame(ref_points)
    ij=((0,1),(0,2),(1,2))
    cd=[math.acos(max(-1.0,min(1.0,dot(cb[i],cb[j])))) for i,j in ij]
    rd=[math.acos(max(-1.0,min(1.0,dot(rb[i],rb[j])))) for i,j in ij]
    if max(abs(a-b) for a,b in zip(cd,rd))>0.09:
        raise ValueError("feature shape changed")
    if arm == "raw_pixels":
        yaw, pitch = raw_error(cur_points, ref_points)
    elif arm == "spherical_features":
        yaw, pitch, _, _ = rotation_error(cur_points, ref_points)
    else:
        raise ValueError("unknown image-only arm")
    if max(abs(yaw), abs(pitch)) <= STOP_TOL:
        return None
    return (max(-ACTION_LIMIT, min(ACTION_LIMIT, -GAIN*yaw)),
            max(-ACTION_LIMIT, min(ACTION_LIMIT, -GAIN*pitch)))
