// Frozen independent auditor for Issue #8640 A02. It reconstructs every mask from raw worlds.
const N=8,H=3;
const F={
 complete:{y:{A:[1,1,1,1,1,1,0,0],B:[1,1,0,0,0,0,0,0]},s:{A:Array(8).fill("routine"),B:Array(8).fill("routine")},pt:{A:Array(8).fill(1),B:Array(8).fill(1)},pl:{A:Array(8).fill(1),B:Array(8).fill(1)},d:{A:Array(8).fill(1),B:Array(8).fill(1)}},
 route_dependent:{y:{A:[1,1,1,1,1,1,0,0],B:[1,1,0,0,0,0,0,0]},s:{A:[...Array(6).fill("slow_confirmation"),"explicit_error","explicit_error"],B:Array(8).fill("routine")},pt:{A:[...Array(6).fill(.05),1,1],B:Array(8).fill(1)},pl:{A:[...Array(6).fill(.05),1,1],B:Array(8).fill(1)},d:{A:Array(8).fill(1),B:Array(8).fill(1)}},
 fixed_horizon:{y:{A:[1,1,1,1,1,1,0,0],B:[1,1,0,0,0,0,0,0]},s:{A:Array(8).fill("routine"),B:Array(8).fill("routine")},pt:{A:Array(8).fill(1),B:Array(8).fill(1)},pl:{A:Array(8).fill(1),B:Array(8).fill(1)},d:{A:[5,5,5,5,5,5,1,1],B:[1,1,5,5,5,5,5,5]}},
 zero_probability:{y:{A:[1,1,0,0,0,0,0,0],B:[1,1,1,1,0,0,0,0]},s:{A:["observed_success","observed_success",...Array(6).fill("never_checked")],B:Array(8).fill("routine")},pt:{A:[1,1,0,0,0,0,0,0],B:Array(8).fill(1)},pl:{A:[1,1,0,0,0,0,0,0],B:Array(8).fill(1)},d:{A:[1,1,5,5,5,5,5,5],B:Array(8).fill(1)}},
 hidden_misspecified:{y:{A:[1,1,1,1,1,1,0,0],B:[1,1,0,0,0,0,0,0]},s:{A:Array(8).fill("unlogged_signal"),B:Array(8).fill("routine")},pt:{A:[...Array(6).fill(.1),1,1],B:Array(8).fill(.5)},pl:{A:Array(8).fill(.5),B:Array(8).fill(.5)},d:{A:Array(8).fill(1),B:Array(8).fill(1)}}
};
function eq(a,b){return a===null||b===null?a===b:Math.abs(a-b)<1e-12}
function assert(x,m){if(!x)throw Error(m)}
function auditRaw(raw){
 assert(raw.allocation==="issue-8640-method-a02"&&raw.n===N&&raw.horizon===H,"allocation/fixed dimensions");
 assert(raw.scenarios.length===5,"scenario count");
 const out={};
 for(const sc of raw.scenarios){
  const name=sc.summary.scenario,f=F[name];assert(f&&!out[name],"scenario identity");
  const cfg=sc.config;
  for(const r of ["A","B"])for(let i=0;i<N;i++){
   assert(cfg.y[r][i]===f.y[r][i]&&cfg.signal[r][i]===f.s[r][i],"fixture outcome/signal");
   assert(cfg.pt[r][i]===f.pt[r][i]&&cfg.pl[r][i]===f.pl[r][i],"fixture propensity");
   assert(cfg.d[r][i]===f.d[r][i],"fixture delay");
  }
  const worlds=sc.worlds,seen=new Set();assert(worlds.length===4096,"world roster");
  let mass=0,rev=0;const rn={A:0,B:0},rd={A:0,B:0},im={A:0,B:0},valid={A:true,B:true},bc={A:0,B:0};
  const truth={A:f.y.A.reduce((a,b)=>a+b,0)/N,B:f.y.B.reduce((a,b)=>a+b,0)/N};
  for(const w of worlds){
   const [a,m,p]=w;assert(Number.isInteger(a)&&a>=0&&a<16&&Number.isInteger(m)&&m>=0&&m<256,"world keys");
   const k=a+":"+m;assert(!seen.has(k),"duplicate assignment/mask");seen.add(k);
   const rows=[];
   for(let i=0;i<N;i++){
    const bit=(a>>(i>>1))&1,route=i%2===0?(bit===0?"A":"B"):(bit===0?"B":"A");
    const observed=((m>>i)&1)===1,timely=f.d[route][i]<=H,q=timely?f.pt[route][i]:0;
    rows.push({i,route,observed,timely});
   }
   let expectedP=1/16;
   for(const z of rows){const q=z.timely?f.pt[z.route][z.i]:0;expectedP*=z.observed?q:1-q;}
   assert(eq(p,expectedP),"world probability");mass+=p;
   let rate={};
   for(const r of ["A","B"]){
    const obs=rows.filter(z=>z.route===r&&z.observed),succ=obs.reduce((s,z)=>s+f.y[r][z.i],0);
    rate[r]=obs.length?succ/obs.length:null;
    const lo=succ/N,hi=(succ+N-obs.length)/N;
    assert(lo<=truth[r]&&truth[r]<=hi,"partial-identification bounds miss truth");
    let canWeight=Array.from({length:N},(_,i)=>f.pl[r][i]>0&&f.d[r][i]<=H).every(Boolean),est=0;
    for(const z of obs){const q=z.timely?f.pl[r][z.i]:0;if(q<=0)canWeight=false;else est+=f.y[r][z.i]/(.5*q*N);}
    if(!canWeight&&p>0)valid[r]=false;
    if(canWeight)im[r]+=p*est;
    if(rate[r]!==null){rn[r]+=p*rate[r];rd[r]+=p;}
    bc[r]+=p;
   }
   const reversal=rate.A!==null&&rate.B!==null&&rate.A<rate.B;
   if(reversal)rev+=p;
  }
  assert(seen.size===4096&&eq(mass,1),"complete enumeration/mass");
  const s=sc.summary;
  assert(s.worlds===4096&&s.horizon===H&&eq(s.probabilityMass,1),"summary frame");
  assert(eq(s.reversalProbability,rev),"reversal summary");
  for(const r of ["A","B"]){
   assert(eq(s.truth[r],truth[r]),"population mean");
   assert(eq(s.meanResolved[r],rd[r]?rn[r]/rd[r]:null),"resolved-only expectation");
   assert(eq(s.expectedIPW[r],valid[r]?im[r]:null),"logged IPW expectation");
   assert(eq(s.ipwBias[r],valid[r]?im[r]-truth[r]:null),"IPW bias");
   assert(s.ipwDefined[r]===valid[r]&&eq(s.boundsCoverMass[r],bc[r]),"identification/bounds summary");
  }
  out[name]={worlds:seen.size,mass,truth,reversalProbability:rev,expectedIPW:s.expectedIPW,ipwBias:s.ipwBias,boundsCoverMass:bc};
 }
 assert(out.complete.reversalProbability===0,"complete ascertainment negative control");
 assert(out.route_dependent.reversalProbability>0,"planted rank reversal");
 for(const r of ["A","B"])assert(eq(out.route_dependent.expectedIPW[r],out.route_dependent.truth[r]),"correct logged IPW control");
 assert(out.fixed_horizon.expectedIPW.A===null&&out.zero_probability.expectedIPW.A===null,"positivity failure incorrectly weighted");
 assert(Math.abs(out.hidden_misspecified.ipwBias.A)>0.1,"mislogged propensity missed");
 return out;
}
function runAudit(raw){
 const scenarios=auditRaw(raw),tests={
  drop_world:d=>d.scenarios[0].worlds.pop(),
  false_observation:d=>{d.scenarios[1].worlds[0][1]^=1},
  mislogged_probability:d=>{d.scenarios[1].config.pl.A[0]=.91},
  changed_horizon:d=>{d.horizon=H+1},
  hide_zero_probability:d=>{d.scenarios[3].config.pt.A[2]=.25}
 },mutations={};
 for(const [name,mutate] of Object.entries(tests)){const d=JSON.parse(JSON.stringify(raw));mutate(d);
  try{auditRaw(d);mutations[name]="ACCEPTED_UNEXPECTEDLY"}catch(_){mutations[name]="REJECTED"}}
 const rejected=Object.values(mutations).filter(x=>x==="REJECTED").length;
 return {allocation:"issue-8640-method-a02",status:rejected===5?"PASS_METHOD_SCOPED":"FAIL_MUTATION_ACCEPTED",
  independentRawAudit:"PASS",scenarios,mutations,mutationRejected:rejected,mutationTotal:5,
  scope:"finite synthetic identification method only; no historical or live inference"};
}
