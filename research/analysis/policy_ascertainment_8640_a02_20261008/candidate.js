// Frozen corrected candidate for Issue #8640 A02. Exact enumeration only.
const N=8,H=3;
const configs={
 complete:{y:{A:[1,1,1,1,1,1,0,0],B:[1,1,0,0,0,0,0,0]},
  signal:{A:Array(8).fill("routine"),B:Array(8).fill("routine")},
  pt:{A:Array(8).fill(1),B:Array(8).fill(1)},pl:{A:Array(8).fill(1),B:Array(8).fill(1)},
  d:{A:Array(8).fill(1),B:Array(8).fill(1)}},
 route_dependent:{y:{A:[1,1,1,1,1,1,0,0],B:[1,1,0,0,0,0,0,0]},
  signal:{A:[...Array(6).fill("slow_confirmation"),"explicit_error","explicit_error"],B:Array(8).fill("routine")},
  pt:{A:[...Array(6).fill(.05),1,1],B:Array(8).fill(1)},
  pl:{A:[...Array(6).fill(.05),1,1],B:Array(8).fill(1)},
  d:{A:Array(8).fill(1),B:Array(8).fill(1)}},
 fixed_horizon:{y:{A:[1,1,1,1,1,1,0,0],B:[1,1,0,0,0,0,0,0]},
  signal:{A:Array(8).fill("routine"),B:Array(8).fill("routine")},
  pt:{A:Array(8).fill(1),B:Array(8).fill(1)},pl:{A:Array(8).fill(1),B:Array(8).fill(1)},
  d:{A:[5,5,5,5,5,5,1,1],B:[1,1,5,5,5,5,5,5]}},
 zero_probability:{y:{A:[1,1,0,0,0,0,0,0],B:[1,1,1,1,0,0,0,0]},
  signal:{A:["observed_success","observed_success",...Array(6).fill("never_checked")],B:Array(8).fill("routine")},
  pt:{A:[1,1,0,0,0,0,0,0],B:Array(8).fill(1)},
  pl:{A:[1,1,0,0,0,0,0,0],B:Array(8).fill(1)},
  d:{A:[1,1,5,5,5,5,5,5],B:Array(8).fill(1)}},
 hidden_misspecified:{y:{A:[1,1,1,1,1,1,0,0],B:[1,1,0,0,0,0,0,0]},
  signal:{A:Array(8).fill("unlogged_signal"),B:Array(8).fill("routine")},
  pt:{A:[...Array(6).fill(.1),1,1],B:Array(8).fill(.5)},
  pl:{A:Array(8).fill(.5),B:Array(8).fill(.5)},
  d:{A:Array(8).fill(1),B:Array(8).fill(1)}}
};
function evaluate(name,cfg){
 const worlds=[],truth={A:cfg.y.A.reduce((a,b)=>a+b,0)/N,B:cfg.y.B.reduce((a,b)=>a+b,0)/N};
 const rnum={A:0,B:0},rden={A:0,B:0},imean={A:0,B:0},valid={A:true,B:true},boundsMass={A:0,B:0};
 let mass=0,reversal=0;
 for(let a=0;a<16;a++)for(let m=0;m<256;m++){
  const rows=[];let prob=1/16;
  for(let i=0;i<N;i++){
   const pair=Math.floor(i/2),bit=(a>>pair)&1;
   const route=i%2===0?(bit===0?"A":"B"):(bit===0?"B":"A");
   const observed=((m>>i)&1)===1,timely=cfg.d[route][i]<=H,q=timely?cfg.pt[route][i]:0;
   prob*=observed?q:1-q;
   rows.push({i,route,observed});
  }
  let rate={},est={},lo={},hi={};
  for(const route of ["A","B"]){
   const obs=rows.filter(x=>x.route===route&&x.observed);
   const successes=obs.reduce((s,x)=>s+cfg.y[route][x.i],0);
   rate[route]=obs.length?successes/obs.length:null;
   lo[route]=successes/N;hi[route]=(successes+N-obs.length)/N;
   let ok=Array.from({length:N},(_,i)=>cfg.pl[route][i]>0&&cfg.d[route][i]<=H).every(Boolean),v=0;
   for(const x of obs){const q=cfg.d[route][x.i]<=H?cfg.pl[route][x.i]:0;if(q<=0)ok=false;else v+=cfg.y[route][x.i]/(.5*q*N);}
   est[route]=ok?v:null;
   if(rate[route]!==null){rnum[route]+=prob*rate[route];rden[route]+=prob;}
   if(est[route]===null){if(prob>0)valid[route]=false;}else imean[route]+=prob*est[route];
   if(!(lo[route]<=truth[route]&&truth[route]<=hi[route]))throw Error("bounds missed truth");
   boundsMass[route]+=prob;
  }
  const rev=rate.A!==null&&rate.B!==null&&rate.A<rate.B;
  if(rev)reversal+=prob;
  worlds.push([a,m,prob]);
  mass+=prob;
 }
 const summary={scenario:name,truth,worlds:worlds.length,probabilityMass:mass,reversalProbability:reversal,
  meanResolved:{},expectedIPW:{},ipwBias:{},ipwDefined:valid,boundsCoverMass:boundsMass,horizon:H};
 for(const r of ["A","B"]){summary.meanResolved[r]=rden[r]?rnum[r]/rden[r]:null;
  summary.expectedIPW[r]=valid[r]?imean[r]:null;summary.ipwBias[r]=valid[r]?imean[r]-truth[r]:null;}
 return {summary,config:cfg,worlds};
}
function runCandidate(){return {allocation:"issue-8640-method-a02",n:N,horizon:H,
 assignment:"four blocked pairs; within each pair one unit randomized to A and one to B with probability 1/2",
 scenarios:Object.keys(configs).map(k=>evaluate(k,configs[k])),
 scope:"exact finite synthetic identification method only; no historical/live inference"};}
