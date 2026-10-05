"""Deterministic independent exactness stress; not GUI or efficacy evidence."""
import argparse
import json
from pathlib import Path
import numpy as np
from tile_transport import Encoder, Decoder, Frame


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--out",type=Path,required=True); args=ap.parse_args()
    rng=np.random.default_rng(918273)
    frames=0; packets=0; sparse=0; resets=0
    for size in (1,7,16,64,128):
        for mode,channels in (("L",1),("RGB",3),("RGBA",4)):
            encs={s:Encoder("stress",s,size) for s in ("O1","O2")}
            decs={s:Decoder("stress") for s in encs}
            for step in range(80):
                if step%20==0:
                    h,w=int(rng.integers(1,90)),int(rng.integers(1,90))
                    array=rng.integers(0,256,(h,w,channels),dtype=np.uint8)
                elif step%11==0: array=rng.integers(0,256,array.shape,dtype=np.uint8)
                elif step%3:
                    for _ in range(int(rng.integers(1,9))):
                        array[int(rng.integers(h)),int(rng.integers(w)),int(rng.integers(channels))] ^= 1
                frame=Frame(w,h,mode,array.tobytes()); frames+=1
                wires={}
                for s,encoder in encs.items():
                    context=(("step",step),("focus",step%5))
                    wire=encoder.encode(frame,action_id=str(step),observed_ns=step,context=context)
                    restored=decs[s].accept(wire); packets+=1
                    assert (restored.width,restored.height,restored.mode)==(w,h,mode)
                    assert np.array_equal(np.frombuffer(restored.pixels,np.uint8).reshape(array.shape),array)
                    assert decs[s].metadata["context"]==[["step",step],["focus",step%5]]
                    wires[s]=wire
                    sparse+=int(encoder.last["kind"]=="tiles")
                assert len(wires["O2"])<=len(wires["O1"])
                if step%19==0:
                    for s in encs:
                        encs[s]=Encoder("stress",s,size); decs[s]=Decoder("stress")
                    resets+=1
    result=dict(seed=918273,source_frames=frames,decoded_packets=packets,tiles_packets=sparse,
                paired_resets=resets,errors=0,scope="synthetic functional stress, not live task evidence")
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open("x") as out: json.dump(result,out,indent=2)
    print(json.dumps(result))


if __name__=="__main__": main()
