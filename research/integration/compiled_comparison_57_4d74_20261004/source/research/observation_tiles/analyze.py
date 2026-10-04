"""Independent archived-packet/source audit and paired A2 summaries."""
import argparse
import hashlib
import json
from pathlib import Path
from time import perf_counter_ns
import numpy as np
from PIL import Image
from tile_transport import Decoder, Encoder, Frame
import gui_suite as suite


def quantiles(values):
    return dict(zip(("p50","p95","p99"),np.quantile(values,[.5,.95,.99]).tolist()))


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("runs",nargs="+",type=Path)
    ap.add_argument("--out",type=Path,required=True); args=ap.parse_args()
    pairs={}; all_rows=[]; common=None; samples=0
    encode={"O1":[],"O2":[]}; decode={"O1":[],"O2":[]}; feedback={"O1":[],"O2":[]}
    for run in args.runs:
        env=json.loads((run/"environment.json").read_text())
        identity={k:env[k] for k in ("versions","transport_sources","transport_parameters")}
        if common is None: common=identity
        assert identity==common,"Mixed freeze/version"
        schedule=json.loads((run/"schedule.json").read_text())
        if schedule["phase"]=="fresh":
            frozen=json.loads(Path(schedule["manifest"]).read_text())
            assert {k:frozen[k] for k in identity}==identity,"Run differs from freeze"
        expected={(app,seed,strategy) for app,seed in schedule["pairs"] for strategy in ("O1","O2")}
        rows=[json.loads(x) for x in (run/"runs.jsonl").read_text().splitlines()]
        assert len(rows)==len(expected) and {(r["app"],r["seed"],r["strategy"]) for r in rows}==expected
        assert json.loads((run/"COMPLETE.json").read_text())["success"]==len(rows)
        for row in rows:
            assert row["success"] and row["audit_pass"] and row["wire_reconstruction_errors"]==0
            path=run/row["relative_path"]; strategy=row["strategy"]
            observations=[json.loads(x) for x in (path/"observations.jsonl").read_text().splitlines()]
            wires=json.loads((path/"wire.json").read_text())
            assert len(wires)==len(observations)==row["candidate_observations"]
            dec=Decoder(f'{row["app"]}-{row["seed"]}-{strategy}')
            counter={s:Encoder("counterfactual",s,64) for s in ("O1","O2")}
            total={s:0 for s in counter}; actual_bytes=0
            for i,(record,stats) in enumerate(zip(observations,wires),1):
                with Image.open(path/"frames"/(record["sha256"]+".png")) as image:
                    source=Frame(image.width,image.height,image.mode,image.tobytes())
                digest=hashlib.sha256(f"{source.width},{source.height},{source.mode}:".encode()+source.pixels).hexdigest()
                assert digest==record["sha256"]
                wire=(path/f"{i:03d}.ait").read_bytes()
                assert len(wire)==stats["wire_bytes"]
                restored=dec.accept(wire)
                assert (restored.width,restored.height,restored.mode)==(source.width,source.height,source.mode)
                assert np.array_equal(np.frombuffer(restored.pixels,np.uint8),np.frombuffer(source.pixels,np.uint8))
                for name in ("action_id","observed_ns","context"):
                    assert dec.metadata[name]==record[name]
                actual_bytes+=len(wire); samples+=1
                for name,enc in counter.items():
                    total[name]+=len(enc.encode(source,action_id=record["action_id"],observed_ns=record["observed_ns"],context=record["context"]))
                encode[strategy].append(stats["encode_ns"]/1e6); decode[strategy].append(stats["decode_ns"]/1e6)
            assert actual_bytes==row["wire_bytes"]
            output=path/{"xterm":"submitted.txt","chromium":"submitted.txt","calc":"sheet.xlsx","inkscape":"shape.svg"}[row["app"]]
            assert suite.evaluate(row["app"],output,row["goal"])["success"],"Independent output rescore failed"
            actions=json.loads((path/"actions.json").read_text())
            feedback[strategy].extend(a["first_feedback_ms"] for a in actions)
            key=(str(run),row["app"],row["seed"])
            pairs.setdefault(key,{})[strategy]=dict(row=row,same=total,actions=[a["action_id"] for a in actions])
            all_rows.append(row)
    live=[]; same=[]; wall=[]
    for pair in pairs.values():
        a,b=pair["O1"],pair["O2"]
        assert a["actions"]==b["actions"]
        # Setup readiness capture count is nondeterministic and not a goal.
        # Ephemeral loopback HTTP ports are freshly allocated per reset.
        ga={k:v for k,v in a["row"]["goal"].items() if k not in ("setup_readiness_captures","url")}
        gb={k:v for k,v in b["row"]["goal"].items() if k not in ("setup_readiness_captures","url")}
        assert ga==gb
        for key in ("logical_ops","input_events"): assert a["row"][key]==b["row"][key]
        live.append([a["row"]["wire_bytes"],b["row"]["wire_bytes"]])
        same.append([a["same"][s]+b["same"][s] for s in ("O1","O2")])
        wall.append(b["row"]["task_wall_ms"]-a["row"]["task_wall_ms"])
    rng=np.random.default_rng(65537); indexes=rng.integers(0,len(pairs),(10000,len(pairs)))
    def reduction(values):
        values=np.array(values); sums=values.sum(axis=0); boot=values[indexes].sum(axis=1)
        return dict(o1_bytes=int(sums[0]),o2_bytes=int(sums[1]),reduction_percent=float(100*(1-sums[1]/sums[0])),
                    ci95_percent=np.quantile(100*(1-boot[:,1]/boot[:,0]),[.025,.975]).tolist())
    wall=np.array(wall)
    summary=dict(episodes=len(all_rows),pairs=len(pairs),sampled_frames=samples,audit_errors=0,
                 correctness_gate="PASS",live_wire=reduction(live),same_trace_wire=reduction(same),
                 paired_wall_delta_ms=dict(median=float(np.median(wall)),ci95=np.quantile(np.median(wall[indexes],axis=1),[.025,.975]).tolist()),
                 encode_ms={s:quantiles(v) for s,v in encode.items()},decode_ms={s:quantiles(v) for s,v in decode.items()},
                 first_feedback_ms={s:quantiles(v) for s,v in feedback.items()},
                 scope="serialized local transport, reconstructed full model image; not image-token savings")
    summary["by_app"]={app:{s:dict(episodes=sum(r["app"]==app and r["strategy"]==s for r in all_rows),
                                    wire_bytes=sum(r["wire_bytes"] for r in all_rows if r["app"]==app and r["strategy"]==s))
                           for s in ("O1","O2")} for app in suite.APPS}
    args.out.mkdir(parents=True,exist_ok=False); suite.write_json(args.out/"summary.json",summary)
    print(json.dumps(summary,indent=2))


if __name__=="__main__": main()
