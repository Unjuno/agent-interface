"""Local stdin JSON interface for a human/model-driven isolated GUI session.

The assistant chooses actions from reconstructed screenshots. No scripted task
controller runs. Input acknowledgment never means semantic completion. Finish
ends control before the independent saved-output evaluator runs.
"""
import argparse
import json
import shutil
import sys
import time
import traceback
from pathlib import Path
from PIL import ImageGrab

from tile_transport import Encoder, Decoder, Frame
import gui_suite as suite


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--app",choices=suite.APPS,required=True)
    ap.add_argument("--seed",type=int,required=True)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--chromium",default="/home/taka/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome")
    args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=False)
    session=None; server=None; output=None; events=[]; records=[]
    def emit(value):
        events.append(value)
        print(json.dumps(value),flush=True)
    try:
        session=suite.Session()
        goal,output,server=suite.prepare(session,args.app,args.seed,args.chromium)
        driver=suite.base.Driver(session,0)
        enc=Encoder("dogfood","O2",64); dec=Decoder("dogfood")
        def observe(action_id):
            started=time.perf_counter_ns()
            im=ImageGrab.grab(xdisplay=session.name).convert("RGB")
            captured=time.perf_counter_ns()
            source=Frame(im.width,im.height,im.mode,im.tobytes())
            context=session.context(); context_at=time.perf_counter_ns()
            wire=enc.encode(source,action_id=action_id,observed_ns=captured,context=context)
            encoded=time.perf_counter_ns(); frame=dec.accept(wire); ready=time.perf_counter_ns()
            if frame != source: raise AssertionError("Lossless reconstruction failed")
            seq=enc.sequence
            (args.out/f"{seq:03d}.ait").write_bytes(wire)
            path=args.out/f"{seq:03d}.png"
            suite.image_for(frame).save(path)
            archived=time.perf_counter_ns()
            record=dict(event="observation",sequence=seq,action_id=action_id,
                        image=str(path.resolve()),capture_ns=captured,
                        context_observed_ns=context_at,context=context,
                        reconstruction_verified=True,**enc.last,
                        capture_ms=(captured-started)/1e6,
                        decode_ms=(ready-encoded)/1e6,
                        local_feedback_ready_ns=ready,archive_ms=(archived-ready)/1e6,
                        semantic_completion="unknown")
            records.append(record); emit(record)
        emit(dict(event="ready",app=args.app,goal=goal,operations=["observe","text","key","chord","drag","finish"],
                  note="input_ack only acknowledges X11 injection; image and context have separate timestamps"))
        observe("initial")
        for line in sys.stdin:
            command=json.loads(line); op=command["op"]
            action_id=str(command.get("id",len(events)))
            if op=="finish":
                # No more control is possible after entering this branch.
                score=suite.evaluate(args.app,output,goal)
                emit(dict(event="independent_evaluation",**score))
                break
            if op=="observe": observe(action_id); continue
            issued=time.perf_counter_ns()
            if op=="text": driver.text(command["text"])
            elif op=="key": driver.key(command["key"])
            elif op=="chord": driver.chord(command["modifier"],command["key"])
            elif op=="drag": driver.drag(*command["points"])
            else: raise ValueError("Unsupported operation")
            ack=time.perf_counter_ns()
            emit(dict(event="input_ack",action_id=action_id,issued_ns=issued,
                      acknowledged_ns=ack,injection_ms=(ack-issued)/1e6,
                      semantic_completion="unknown"))
            observe(action_id)
    except Exception:
        emit(dict(event="error",traceback=traceback.format_exc()))
        raise
    finally:
        if output is not None and output.exists(): shutil.copy2(output,args.out/output.name)
        suite.write_json(args.out/"events.json",events)
        suite.write_json(args.out/"observations.json",records)
        if server is not None: server.shutdown(); server.server_close()
        if session is not None:
            session.close()
            shutil.rmtree(session.tmp)


if __name__=="__main__": main()
