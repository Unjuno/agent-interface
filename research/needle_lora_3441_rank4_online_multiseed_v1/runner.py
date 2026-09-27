"""Five-seed online LoRA rank-capacity study; deterministic, CPU-only, in-memory."""
import base64, copy, gzip, hashlib, io, json, math, platform, random, statistics, time
import torch
from torch import nn

ALLOCATION = "needle-lora-3441-rank4-online-multiseed-v1"
SEEDS = (3451, 3452, 3453, 3454, 3455)
D, H, C = 8, 16, 4
N_BASE, N_SUPPORT, N_HELDOUT = 512, 16, 4096
BASE_STEPS, STEPS_PER_FEEDBACK = 400, 8
TOTAL_ADAPTER_STEPS = N_SUPPORT * STEPS_PER_FEEDBACK
LR_BASE, LR_ADAPTER = 0.025, 0.04
EPOCH, ROLE_VERSION = 16, 16

def data(n, seed):
    return torch.randn(n, D, generator=torch.Generator(device="cpu").manual_seed(seed))

def labels(x, flip=False):
    a = (x[:, 0] > 0).long()
    if flip: a = 1 - a
    b = (x[:, 1] > 0).long()
    return a * 2 + b

def pack2(values):
    assert len(values) % 4 == 0 and all(0 <= int(v) < 4 for v in values)
    return bytes((int(values[i]) << 6) | (int(values[i+1]) << 4) |
                 (int(values[i+2]) << 2) | int(values[i+3])
                 for i in range(0, len(values), 4))

class Core(nn.Module):
    def __init__(self):
        super().__init__()
        self.enc = nn.Sequential(nn.Linear(D, H), nn.Tanh())
        self.head = nn.Linear(H, C)
    def forward(self, x):
        return self.head(self.enc(x))

class LoRA(nn.Module):
    def __init__(self, core, rank):
        super().__init__()
        self.core, self.rank = core, rank
        for p in core.parameters(): p.requires_grad_(False)
        self.a = nn.Parameter(torch.randn(H, rank) * 0.04)
        self.b = nn.Parameter(torch.zeros(rank, C))
    def forward(self, x):
        h = self.core.enc(x)
        return self.core.head(h) + (h @ self.a @ self.b) / self.rank

def clone_state(model):
    return {k: v.detach().clone() for k, v in model.state_dict().items()}

def exact_state(model, state):
    now = model.state_dict()
    return list(now) == list(state) and all(
        now[k].dtype == state[k].dtype and now[k].shape == state[k].shape
        and torch.equal(now[k], state[k]) for k in state
    )

def fit_base(model, x, y, seed):
    opt = torch.optim.AdamW(model.parameters(), lr=LR_BASE)
    rng = torch.Generator(device="cpu").manual_seed(seed + 10)
    model.train(); started = time.perf_counter_ns()
    for _ in range(BASE_STEPS):
        ix = torch.randint(len(x), (32,), generator=rng)
        loss = nn.functional.cross_entropy(model(x[ix]), y[ix])
        opt.zero_grad(set_to_none=True); loss.backward(); opt.step()
    return (time.perf_counter_ns() - started) / 1e6

def update_steps(model, opt, x, y, seen, rng):
    model.train()
    index_tensor = torch.as_tensor(seen, dtype=torch.long)
    for _ in range(STEPS_PER_FEEDBACK):
        ix = torch.randint(len(seen), (32,), generator=rng)
        batch_ix = index_tensor[ix]
        loss = nn.functional.cross_entropy(model(x[batch_ix]), y[batch_ix])
        opt.zero_grad(set_to_none=True); loss.backward(); opt.step()

def dispatch(role, epoch, version, base, registry):
    if epoch != EPOCH: return "YIELD", None
    if role == "A": return "PROPOSE", base
    if role not in registry and role not in ("B_R2_ONLINE","B_R2_BATCH","B_R4_ONLINE","B_R4_BATCH"):
        return "YIELD", None
    if version != ROLE_VERSION: return "YIELD", None
    model = registry.get(role)
    return ("PROPOSE", model) if model is not None else ("YIELD", None)

def evaluate(role, model, base, registry, epoch, version, x, y):
    decision, chosen = dispatch(role, epoch, version, base, registry)
    if decision != "PROPOSE" or chosen is not model: raise RuntimeError("valid_route_refused")
    chosen.eval()
    with torch.no_grad(): preds = chosen(x).argmax(-1).tolist()
    expected = y.tolist()
    correct = sum(a == b for a,b in zip(expected,preds))
    packed = pack2(preds)
    return {"decision":decision,"requested_role":role,"epoch":epoch,"version":version,
            "selected_adapter":role,"n":len(expected),"correct":correct,
            "accuracy":correct/len(expected),"predicted_b64":base64.b64encode(packed).decode(),
            "predicted_sha256":hashlib.sha256(packed).hexdigest()}

def train_online(model,x,y,seed):
    opt=torch.optim.AdamW([model.a,model.b],lr=LR_ADAPTER)
    order=torch.randperm(N_SUPPORT,generator=torch.Generator(device="cpu").manual_seed(seed+20)).tolist()
    rng=torch.Generator(device="cpu").manual_seed(seed+21)
    seen=[]; update_ms=[]; curve=[]
    for count,row in enumerate(order,start=1):
        seen.append(row); started=time.perf_counter_ns()
        update_steps(model,opt,x,y,seen,rng)
        update_ms.append((time.perf_counter_ns()-started)/1e6)
        if count in (1,2,4,8,12,16):
            model.eval()
            with torch.no_grad(): correct=int((model(HELDOUT_X)==HELDOUT_Y).sum().item())
            curve.append({"feedback_seen":count,"correct":correct,"n":N_HELDOUT,"accuracy":correct/N_HELDOUT})
    return update_ms,curve

def train_batch(model,x,y,seed):
    opt=torch.optim.AdamW([model.a,model.b],lr=LR_ADAPTER)
    rng=torch.Generator(device="cpu").manual_seed(seed+22)
    model.train(); started=time.perf_counter_ns()
    for _ in range(TOTAL_ADAPTER_STEPS):
        ix=torch.randint(N_SUPPORT,(32,),generator=rng)
        loss=nn.functional.cross_entropy(model(x[ix]),y[ix])
        opt.zero_grad(set_to_none=True); loss.backward(); opt.step()
    return (time.perf_counter_ns()-started)/1e6

def pct95(xs):
    return sorted(xs)[math.ceil(0.95*len(xs))-1]

def main():
    global HELDOUT_X, HELDOUT_Y
    torch.set_num_threads(1); torch.use_deterministic_algorithms(True)
    records=[]
    for seed in SEEDS:
        random.seed(seed); torch.manual_seed(seed)
        xa,xb,ea,eb=[data(n,seed+i) for i,n in enumerate((N_BASE,N_SUPPORT,N_HELDOUT,N_HELDOUT),start=1)]
        ya,yb=labels(xa),labels(xb,True); eya,eyb=labels(ea),labels(eb,True)
        base=Core(); base_ms=fit_base(base,xa,ya,seed); base_before=clone_state(base)
        HELDOUT_X,HELDOUT_Y=eb,eyb
        registry={}; initial_states={}; batch_ms_by_rank={}
        for rank in (2,4):
            torch.manual_seed(seed+30+rank)
            template=LoRA(base,rank); initial=clone_state(template); initial_states[rank]=initial
            online=LoRA(base,rank); batch=LoRA(base,rank)
            online.load_state_dict(initial); batch.load_state_dict(initial)
            online_ms,curve=train_online(online,xb,yb,seed)
            batch_ms=train_batch(batch,xb,yb,seed); batch_ms_by_rank[rank]=batch_ms
            registry[f"B_R{rank}_ONLINE"]=online
            registry[f"B_R{rank}_BATCH"]=batch
            if rank==4:
                learned=clone_state(online); learned_payload=io.BytesIO(); torch.save(learned,learned_payload)
                loaded=torch.load(io.BytesIO(learned_payload.getvalue()),map_location="cpu",weights_only=True)
                online.load_state_dict(loaded); roundtrip=exact_state(online,learned)
                online.load_state_dict(initial); rollback=exact_state(online,initial)
                online.load_state_dict(learned)
                snapshot={"roundtrip_exact":roundtrip,"rollback_exact":rollback,
                          "initial_sha256":hashlib.sha256(snapshot_bytes(initial)).hexdigest(),
                          "learned_sha256":hashlib.sha256(snapshot_bytes(learned)).hexdigest(),
                          "bytes":len(learned_payload.getvalue())}
            if rank==2:
                r2_online_ms,r2_curve=online_ms,curve
            else:
                r4_online_ms,r4_curve=online_ms,curve
            # retain model objects after temporary snapshot rollback
        metrics={}
        for role,model,x,y in (
            ("A",base,ea,eya),
            ("B_R2_ONLINE",registry["B_R2_ONLINE"],eb,eyb),
            ("B_R2_BATCH",registry["B_R2_BATCH"],eb,eyb),
            ("B_R4_ONLINE",registry["B_R4_ONLINE"],eb,eyb),
            ("B_R4_BATCH",registry["B_R4_BATCH"],eb,eyb),
        ):
            metrics[role]=evaluate(role,model,base,registry,EPOCH,ROLE_VERSION,x,y)
        controls={
            "unknown_role":dispatch("B_UNKNOWN",EPOCH,ROLE_VERSION,base,registry)[0],
            "stale_epoch":dispatch("B_R4_ONLINE",EPOCH-1,ROLE_VERSION,base,registry)[0],
            "wrong_version":dispatch("B_R4_ONLINE",EPOCH,ROLE_VERSION+1,base,registry)[0],
        }
        no_adapter=dict(registry); del no_adapter["B_R4_ONLINE"]
        controls["missing_adapter"]=dispatch("B_R4_ONLINE",EPOCH,ROLE_VERSION,base,no_adapter)[0]
        records.append({
            "seed":seed,"base_pretrain_ms":base_ms,"metrics":metrics,
            "online_update_ms":{"rank2":r2_online_ms,"rank4":r4_online_ms},
            "learning_curve":{"rank2":r2_curve,"rank4":r4_curve},
            "batch_train_ms":batch_ms_by_rank,
            "rank4_snapshot":snapshot,"invalid_route_controls":controls,
            "base_immutable":exact_state(base,base_before),
            "expected_labels_b64":base64.b64encode(pack2(eyb.tolist())).decode(),
            "expected_labels_sha256":hashlib.sha256(pack2(eyb.tolist())).hexdigest(),
        })
    out={
        "allocation":ALLOCATION,"seeds":list(SEEDS),
        "environment":{"platform":platform.platform(),"python":platform.python_version(),
                       "torch":torch.__version__,"device":"cpu","threads":torch.get_num_threads(),
                       "deterministic":torch.are_deterministic_algorithms_enabled()},
        "frozen_design":{"base_rows":N_BASE,"support_rows":N_SUPPORT,"heldout_rows":N_HELDOUT,
                         "base_steps":BASE_STEPS,"updates_per_arrival":STEPS_PER_FEEDBACK,
                         "total_adapter_steps":TOTAL_ADAPTER_STEPS,"ranks":[2,4],
                         "arms":["rank2_online","rank2_batch","rank4_online","rank4_batch"]},
        "records":records,
        "scope":"synthetic role-adaptation capacity comparison; no runtime authority",
    }
    raw=json.dumps(out,sort_keys=True,separators=(",",":")).encode()
    envelope={"result_sha256":hashlib.sha256(raw).hexdigest(),"result_bytes":len(raw),
              "result_gzip_b64":base64.b64encode(gzip.compress(raw,mtime=0)).decode()}
    print(json.dumps(envelope,sort_keys=True,separators=(",",":")))

def snapshot_bytes(state):
    buf=io.BytesIO(); torch.save(state,buf); return buf.getvalue()

if __name__=="__main__": main()
