import base64, hashlib, json, math, pathlib

N=128
CENTER=64

def frame(radius=11.0, cx=64.0, cy=64.0, marker_scale=1.0, target_color=230, occlude=False):
    p=bytearray([20])*(N*N)
    def disk(x0,y0,r,color):
        lo_x=max(0,int(math.floor(x0-r-1))); hi_x=min(N-1,int(math.ceil(x0+r+1)))
        lo_y=max(0,int(math.floor(y0-r-1))); hi_y=min(N-1,int(math.ceil(y0+r+1)))
        for y in range(lo_y,hi_y+1):
            for x in range(lo_x,hi_x+1):
                if (x-x0)**2+(y-y0)**2 <= r*r:
                    p[y*N+x]=color
    for mx,my in ((34,34),(94,34),(34,94),(94,94)):
        disk(CENTER+(mx-CENTER)*marker_scale,CENTER+(my-CENTER)*marker_scale,2.2*marker_scale,100)
    disk(cx,cy,radius,target_color)
    if occlude:
        for y in range(52,77):
            for x in range(64,80):
                if p[y*N+x] == target_color: p[y*N+x]=20
    return f"P5\n{N} {N}\n255\n".encode()+bytes(p)

def seq(cid, kind, radii=None, centers=None, marker_scales=None, tracks=None, times=None, occlude_at=None):
    if times is None: times=[round(.1*i,3) for i in range(5)]
    frames=[]
    for i in range(5):
        r=(radii or [11]*5)[i]; x,y=(centers or [(64,64)]*5)[i]
        ms=(marker_scales or [1]*5)[i]
        b=frame(r,x,y,ms,occlude=(occlude_at is not None and i>=occlude_at))
        frames.append({"t_s":times[i],"track_id":(tracks or ["target-1"]*5)[i],"sha256":hashlib.sha256(b).hexdigest(),"pgm_b64":base64.b64encode(b).decode()})
    return {"sequence_id":cid,"source_id":"fixture-session-1","frames":frames}

approaches=[]
for j,tau0 in enumerate((3.0,3.2,3.4,3.6,3.8,4.0),1):
    k=11.0*tau0
    rs=[k/(tau0-.1*i) for i in range(5)]
    approaches.append(seq(f"approach-{j}","approach",radii=rs))
obs={"schema":"looming-image-only-observations-a02-v1","frame_size":[N,N],"sample_period_s":.1,"sequences":approaches}
twin={**approaches[0],"sequence_id":"animation-twin-1","source_id":"fixture-session-1"}
camera=seq("camera-zoom-1","camera_zoom",radii=[11,11.33,11.69,12.06,12.47],marker_scales=[1,1.03,1.063,1.096,1.13])
lateral=seq("lateral-1","lateral",centers=[(44,64),(49,64),(54,64),(59,64),(64,64)])
occluded=seq("occlusion-1","occlusion",radii=[11,11.25,11.52,11.82,12.13],occlude_at=3)
swap=seq("track-swap-1","track_swap",radii=[11,11.25,11.52,11.82,12.13],tracks=["target-A","target-A","target-A","target-B","target-B"])
badtime=seq("timestamp-regression-1","timestamp_regression",radii=[11,11.25,11.52,11.82,12.13],times=[0,.1,.2,.15,.4])
static=seq("static-hazard-1","nonlooming_hazard",radii=[11]*5)
obs["sequences"] += [twin,camera,lateral,occluded,swap,badtime,static]
truth={"schema":"looming-hidden-scorer-a02-v1","contact_cases":{},"control_labels":{
"animation-twin-1":"nonapproach_visual_animation_with_pixels_identical_to_approach-1",
"camera-zoom-1":"global_camera_zoom_without_target_approach",
"lateral-1":"lateral_pass_without_radial_approach",
"occlusion-1":"target_partially_occluded",
"track-swap-1":"target_track_identity_changes",
"timestamp-regression-1":"nonmonotonic_capture_clock",
"static-hazard-1":"visible_nonlooming_hazard"}}
for j,tau0 in enumerate((3.0,3.2,3.4,3.6,3.8,4.0),1):
    truth["contact_cases"][f"approach-{j}"]={"class":"centered_constant_speed_approach","contact_at_s":tau0,"last_frame_s":.4}

root=pathlib.Path(__file__).parent.parent
(root/"candidate_input"/"observations.json").write_text(json.dumps(obs,sort_keys=True,separators=(",",":"))+"\n")
(root/"audit_input"/"observations.json").write_text(json.dumps(obs,sort_keys=True,separators=(",",":"))+"\n")
(root/"audit_input"/"truth.json").write_text(json.dumps(truth,sort_keys=True,separators=(",",":"))+"\n")
