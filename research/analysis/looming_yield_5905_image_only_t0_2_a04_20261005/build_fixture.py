import base64, gzip, hashlib, json, math
from pathlib import Path
N=128; C=64; TIMES=[0.0,.1,.2,.3,.4]

def disk(p,cx,cy,r,v):
    for y in range(max(0,int(cy-r-1)),min(N,int(cy+r+2))):
        for x in range(max(0,int(cx-r-1)),min(N,int(cx+r+2))):
            if (x-cx)**2+(y-cy)**2<=r*r:p[y*N+x]=v

def frame(radius=9,cx=64,cy=64,scale=1,occlude=False):
    p=bytearray([20])*(N*N)
    for mx,my in ((31,31),(97,31),(31,97),(97,97)):
        disk(p,C+(mx-C)*scale,C+(my-C)*scale,2.4*scale,100)
    disk(p,C+(cx-C)*scale,C+(cy-C)*scale,radius*scale,230)
    if occlude:
        # Dark vertical stripe cuts a visible chord from the right half.
        for y in range(50,78):
            for x in range(64,78):
                if p[y*N+x]==230:p[y*N+x]=20
    return f'P5\n{N} {N}\n255\n'.encode()+bytes(p)

def seq(name,radii=None,centers=None,scales=None,tracks=None,times=None,occlude_from=None):
    radii=radii or [9]*5; centers=centers or [(64,64)]*5; scales=scales or [1]*5; tracks=tracks or ['track-1']*5; times=times or TIMES
    fs=[]
    for i in range(5):
        b=frame(radii[i],*centers[i],scales[i],occlude=occlude_from is not None and i>=occlude_from)
        fs.append({'t_s':times[i],'track_id':tracks[i],'sha256':hashlib.sha256(b).hexdigest(),'pgm_b64':base64.b64encode(b).decode('ascii')})
    return {'sequence_id':name,'frames':fs}

approach=[]
contacts=[3.0,3.4,3.8,4.2,4.6,5.0]
r0=[7.0,7.8,8.6,9.4,10.2,11.0]
for i,(tc,r) in enumerate(zip(contacts,r0),1):
    radii=[r*tc/(tc-t) for t in TIMES]
    approach.append(seq(f'approach-{i}',radii=radii))
obs={'schema':'looming-image-only-observations-a04-v1','frame_size':[N,N],'sample_period_s':.1,'sequences':approach}
# The semantic twin has a non-contact label but exactly the same pixels, track IDs and timestamps.
twin=dict(approach[-1]); twin['sequence_id']='animation-twin-6'
controls=[
 seq('camera-zoom-1',radii=[9,9.2,9.4,9.6,9.8],scales=[1,1.025,1.05,1.075,1.10]),
 seq('lateral-1',centers=[(44,64),(49,64),(54,64),(59,64),(64,64)]),
 seq('occlusion-1',radii=[9,9.3,9.6,9.9,10.2],occlude_from=3),
 seq('track-swap-1',radii=[9,9.3,9.6,9.9,10.2],tracks=['A','A','A','B','B']),
 seq('timestamp-regression-1',radii=[9,9.3,9.6,9.9,10.2],times=[0,.1,.2,.15,.4]),
 seq('static-hazard-1'),twin]
obs['sequences']+=controls
truth={'schema':'looming-hidden-scorer-a04-v1','contact_cases':{},'control_labels':{
 'camera-zoom-1':'global_scale_change_no_target_approach','lateral-1':'lateral_pass_without_radial_approach','occlusion-1':'partial_occlusion','track-swap-1':'track_identity_changes','timestamp-regression-1':'nonmonotonic_capture_clock','static-hazard-1':'stationary_nonlooming_hazard','animation-twin-6':'noncontact_world_with_observation_identical_to_approach-6'}}
for i,tc in enumerate(contacts,1):truth['contact_cases'][f'approach-{i}']={'class':'centered_constant_speed_approach','contact_at_s':tc,'last_frame_s':.4}
root=Path(__file__).parent/'inputs';root.mkdir(exist_ok=True)
(root/'observations.json.gz').write_bytes(gzip.compress((json.dumps(obs,sort_keys=True,separators=(',',':'))+'\n').encode('utf8'),mtime=0))
(root/'truth.json.gz').write_bytes(gzip.compress((json.dumps(truth,sort_keys=True,separators=(',',':'))+'\n').encode('utf8'),mtime=0))
