// Frozen independent auditor for Issue #8640 A02; reconstruct from raw only.
const N=4,H=3,PAIRS=[[0,1],[2,3]];
const F={
 complete:{y:{A:[1,1,0,0],B:[1,0,0,0]},s:{A:["routine","routine","routine","routine"],B:["routine","routine","routine","routine"]},pt:{A:[1,1,1,1],B:[1,1,1,1]},pl:{A:[1,1,1,1],B:[1,1,1,1]},d:{A:[1,1,1,1],B:[1,1,1,1]}},
 route_dependent:{y:{A:[1,1,0,0],B:[1,0,0,0]},s:{A:["slow_confirm","slow_confirm","error","error"],B:["routine","routine","routine","routine"]},pt:{A:[.1,.1,1,1],B:[1,1,1,1]},pl:{A:[.1,.1,1,1],B:[1,1,1,1]},d:{A:[1,1,1,1],B:[1,1,1,1]}},
 fixed_horizon:{y:{A:[1,1,0,0],B:[1,0,0,0]},s:{A:["routine","routine","routine","routine"],B:["routine","routine","routine","routine"]},pt:{A:[1,1,1,1],B:[1,1,1,1]},pl:{A:[1,1,1,1],B:[1,1,1,1]},d:{A:[5,5,1,1],B:[1,5,1,1]}},
 zero_probability:{y:{A:[1,0,0,0],B:[1,1,0,0]},s:{A:["seen_success","never","never","never"],B:["routine","routine","routine","routine"]},pt:{A:[1,0,0,0],B:[1,1,1,1]},pl:{A:[1,0,0,0],B:[1,1,1,1]},d:{A:[1,5,5,5],B:[1,1,1,1]}},
 hidden_misspecified:{y:{A:[1,1,0,0],B:[1,0,0,0]},s:{A:["unlogged","unlogged","unlogged","unlogged"],B:["routine","routine","routine","routine"]},pt:{A:[.1,.1,1,1],B:[.5,.5,.5,.5]},pl:{A:[.5,.5,.5,.5],B:[.5,.5,.5,.5]},d:{A:[1,1,1,1],B:[1,1,1,1]}}
};
function eq(a,b){return a===null||b===null?a===b:Math.abs(a-b)<1e-12}
function assert(x,msg){if(!x)throw Error(msg)}
function auditRaw(raw){
 assert(raw.allocation==="issue-8640-method-a02","allocation");
 assert(raw.n===N&&raw.horizon===H,"fixture size/horizon");
 assert(raw.scenarios.length===Object.keys(F).length,"scenario count");
 const output={};
 for(const sc of raw.scenarios){
  const name=sc.summary.scenario, f=F[name];
  assert(!!f&&!output[name],"scenario identity");
  assert(sc.config!==undefined,"missing fixture record");
  const worlds=sc.worlds, seen=new Set();
  assert(worlds.length===64,"world roster");
  let mass=0,rev=0;
  const rn={A:0,B:0},rd={A:0,B:0},ipw={A:0,B:0},iv={A:true,B:true},bc={A:0,B:0};
  const truth={A:f.y.A.reduce((a,b)=>a+b,0)/N,B:f.y.B.reduce((a,b)=>a+b,0)/N};
  for(const w of worlds){
   assert(Number.isInteger(w.assignment)&&w.assignment>=0&&w.assignment<4,"assignment key");
   assert(Number.isInteger(w.mask)&&w.mask>=0&&w.mask<16,"mask key");
   const key=w.assignment+":"+w.mask;assert(!seen.has(key),"duplicate world");seen.add(key);
   let p=.25,route=[];
   for(let i=0;i<N;i++){
    const bit=(w.assignment>>(i>>1))&1;
    route[i]=i%2===0?(bit===0?"A":"B"):(bit===0?"B":"A");
   }
   assert(w.rows.length===N,"attempt frame");
   for(let i=0;i<N;i++){
    const r=w.rows[i],q=(r.delay<=H)?r.pTrue:0,obs=((w.mask>>i)&1)===1;
    assert(r.unit===i&&r.route===route[i],"assignment row");
    assert(r.y===f.y[route[i]][i]&&r.signal===f.s[route[i]][i],"outcome/signal");
    assert(r.pTrue===f.pt[route[i]][i]&&r.pLogged===f.pl[route[i]][i],"selection probability");
    assert(r.delay===f.d[route[i]][i]&&r.timely===(r.delay<=H),"horizon");
    assert(r.observed===obs,"observation mask");
    p*=obs?q:1-q;
   }
   assert(eq(w.prob,p),"world probability");mass+=p;
   let reversal=false;
   for(const routeName of ["A","B"]){
    const obs=w.rows.filter(r=>r.route===routeName&&r.observed);
    const succ=obs.reduce((s,r)=>s+r.y,0),rate=obs.length?succ/obs.length:null;
    const lower=succ/N,upper=(succ+N-obs.length)/N;
    assert(lower<=truth[routeName]&&truth[routeName]<=upper,"partial-identification bounds");
    const z=w.routes[routeName];
    assert(z.n===obs.length&&z.successes===succ&&eq(z.resolved,rate),"resolved-only result");
    assert(eq(z.lower,lower)&&eq(z.upper,upper),"bound arithmetic");
    let valid=Array.from({length:N},(_,i)=>f.pl[routeName][i]>0&&f.d[routeName][i]<=H).every(Boolean);
    let est=0;
    for(const r of obs){const q=r.timely?r.pLogged:0;if(q<=0)valid=false;else est+=r.y/(.5*q*N);}
    assert(eq(z.ipw,valid?est:null),"logged-propensity estimate");
    if(!valid&&p>0)iv[routeName]=false;
    if(rate!==null){rn[routeName]+=p*rate;rd[routeName]+=p;}
    if(valid)ipw[routeName]+=p*est;
    bc[routeName]+=p;
   }
   reversal=w.routes.A.resolved!==null&&w.routes.B.resolved!==null&&w.routes.A.resolved<w.routes.B.resolved;
   assert(w.reversal===reversal,"rank-reversal indicator");
   if(reversal)rev+=p;
  }
  assert(seen.size===64&&eq(mass,1),"complete exact world enumeration");
  const s=sc.summary;
  assert(s.horizon===H&&s.worlds===64&&eq(s.probabilityMass,1),"summary frame");
  assert(eq(s.reversalProbability,rev),"reversal probability");
  assert(JSON.stringify(s.truth)===JSON.stringify(truth),"population truth");
  for(const r of ["A","B"]){
   assert(eq(s.meanResolved[r],rd[r]?rn[r]/rd[r]:null),"resolved expectation");
   assert(eq(s.expectedIPW[r],iv[r]?ipw[r]:null),"IPW expectation");
   assert(eq(s.ipwBias[r],iv[r]?ipw[r]-truth[r]:null),"IPW bias");
   assert(s.ipwDefined[r]===iv[r],"IPW defined flag");
   assert(eq(s.boundsCoverMass[r],bc[r]),"bound coverage mass");
  }
  output[name]={worlds:seen.size,probabilityMass:mass,truth,
   reversalProbability:rev,expectedIPW:s.expectedIPW,ipwBias:s.ipwBias,
   boundsCoverMass:bc};
 }
 assert(output.complete.reversalProbability===0,"invariant ascertainment control");
 assert(output.route_dependent.reversalProbability>0,"planted selection reversal");
 for(const r of ["A","B"])assert(eq(output.route_dependent.expectedIPW[r],output.route_dependent.truth[r]),"positive logged IPW recovery");
 assert(output.fixed_horizon.expectedIPW.A===null&&output.zero_probability.expectedIPW.A===null,"positivity failure must not yield IPW");
 assert(Math.abs(output.hidden_misspecified.ipwBias.A)>0.1,"mislogged propensity negative control");
 return output;
}
function runAudit(raw){
 const checks=auditRaw(raw), corruptions={};
 const cases={
  drop_attempt:d=>d.scenarios[1].worlds[0].rows.pop(),
  false_resolution:d=>{const r=d.scenarios[1].worlds[0].rows[0];r.observed=!r.observed},
  mislogged_probability:d=>{d.scenarios[1].worlds[0].rows[0].pLogged=.91},
  changed_horizon:d=>{d.scenarios[2].summary.horizon=H+1},
  hide_zero_probability:d=>{d.scenarios[3].worlds[0].rows[1].pTrue=.25}
 };
 for(const [name,mutate] of Object.entries(cases)){
  const bad=JSON.parse(JSON.stringify(raw));mutate(bad);
  try{auditRaw(bad);corruptions[name]="ACCEPTED_UNEXPECTEDLY"}
  catch(_){corruptions[name]="REJECTED"}
 }
 return {allocation:"issue-8640-method-a02",status:Object.values(corruptions).every(v=>v==="REJECTED")?"PASS_METHOD_SCOPED":"FAIL_MUTATION_ACCEPTED",
  independentRawAudit:"PASS",scenarios:checks,mutations:corruptions,
  mutationRejected:Object.values(corruptions).filter(v=>v==="REJECTED").length,mutationTotal:Object.keys(corruptions).length,
  limits:"finite synthetic method only; not evidence of historical/live bias"};
}
