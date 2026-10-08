// Frozen candidate for Issue #8640 A02. Exact finite enumeration only.
const N = 4, H = 3;
const configs = {
  complete: {
    y: {A:[1,1,0,0], B:[1,0,0,0]},
    signal:{A:["routine","routine","routine","routine"],B:["routine","routine","routine","routine"]},
    pTrue:{A:[1,1,1,1],B:[1,1,1,1]}, pLogged:{A:[1,1,1,1],B:[1,1,1,1]},
    delay:{A:[1,1,1,1],B:[1,1,1,1]}
  },
  route_dependent: {
    y:{A:[1,1,0,0],B:[1,0,0,0]},
    signal:{A:["slow_confirm","slow_confirm","error","error"],B:["routine","routine","routine","routine"]},
    pTrue:{A:[0.1,0.1,1,1],B:[1,1,1,1]}, pLogged:{A:[0.1,0.1,1,1],B:[1,1,1,1]},
    delay:{A:[1,1,1,1],B:[1,1,1,1]}
  },
  fixed_horizon: {
    y:{A:[1,1,0,0],B:[1,0,0,0]},
    signal:{A:["routine","routine","routine","routine"],B:["routine","routine","routine","routine"]},
    pTrue:{A:[1,1,1,1],B:[1,1,1,1]}, pLogged:{A:[1,1,1,1],B:[1,1,1,1]},
    delay:{A:[5,5,1,1],B:[1,5,1,1]}
  },
  zero_probability: {
    y:{A:[1,0,0,0],B:[1,1,0,0]},
    signal:{A:["seen_success","never","never","never"],B:["routine","routine","routine","routine"]},
    pTrue:{A:[1,0,0,0],B:[1,1,1,1]}, pLogged:{A:[1,0,0,0],B:[1,1,1,1]},
    delay:{A:[1,5,5,5],B:[1,1,1,1]}
  },
  hidden_misspecified: {
    y:{A:[1,1,0,0],B:[1,0,0,0]},
    signal:{A:["unlogged","unlogged","unlogged","unlogged"],B:["routine","routine","routine","routine"]},
    pTrue:{A:[0.1,0.1,1,1],B:[0.5,0.5,0.5,0.5]},
    pLogged:{A:[0.5,0.5,0.5,0.5],B:[0.5,0.5,0.5,0.5]},
    delay:{A:[1,1,1,1],B:[1,1,1,1]}
  }
};
function enumerate(name,cfg) {
  const worlds=[];
  for(let a=0;a<4;a++) for(let m=0;m<16;m++) {
    const rows=[];
    let prob=0.25;
    for(let i=0;i<N;i++) {
      const pair=Math.floor(i/2), bit=(a>>pair)&1;
      const route=(i%2===0) ? (bit===0?"A":"B") : (bit===0?"B":"A");
      const observed=((m>>i)&1)===1, timely=cfg.delay[route][i]<=H;
      const q=timely?cfg.pTrue[route][i]:0;
      prob*=observed?q:1-q;
      rows.push({unit:i,route,y:cfg.y[route][i],signal:cfg.signal[route][i],
        pTrue:cfg.pTrue[route][i],pLogged:cfg.pLogged[route][i],
        delay:cfg.delay[route][i],timely,observed});
    }
    const routes={};
    for(const route of ["A","B"]) {
      const observed=rows.filter(r=>r.route===route&&r.observed);
      const successes=observed.reduce((s,r)=>s+r.y,0);
      const lower=successes/N, upper=(successes+N-observed.length)/N;
      let valid=Array.from({length:N},(_,i)=>
        cfg.pLogged[route][i]>0 && cfg.delay[route][i]<=H).every(Boolean);
      let ipw=0;
      for(const r of observed) {
        const q=r.timely?r.pLogged:0;
        if(q<=0) valid=false;
        else ipw+=r.y/(0.5*q*N);
      }
      routes[route]={n:observed.length,successes,
        resolved:observed.length?successes/observed.length:null,
        ipw:valid?ipw:null,lower,upper};
    }
    worlds.push({assignment:a,mask:m,prob,rows,routes});
  }
  const truth={A:cfg.y.A.reduce((s,x)=>s+x,0)/N,B:cfg.y.B.reduce((s,x)=>s+x,0)/N};
  let reversal=0; const resolvedNum={A:0,B:0},resolvedDen={A:0,B:0},ipwMean={A:0,B:0};
  const ipwValid={A:true,B:true};
  for(const w of worlds) {
    if(w.routes.A.resolved!==null&&w.routes.B.resolved!==null&&w.routes.A.resolved<w.routes.B.resolved) reversal+=w.prob;
    for(const r of ["A","B"]) {
      if(w.routes[r].resolved!==null) {
        resolvedNum[r]+=w.prob*w.routes[r].resolved;
        resolvedDen[r]+=w.prob;
      }
      if(w.routes[r].ipw===null) {
        if(w.prob>0) ipwValid[r]=false;
      } else ipwMean[r]+=w.prob*w.routes[r].ipw;
    }
  }
  const summary={scenario:name,truth,worlds:worlds.length,
    probabilityMass:worlds.reduce((s,w)=>s+w.prob,0),reversalProbability:reversal,
    meanResolved:{},expectedIPW:{},ipwBias:{},ipwIdentified:ipwValid};
  for(const r of ["A","B"]) {
    summary.meanResolved[r]=resolvedDen[r]?resolvedNum[r]/resolvedDen[r]:null;
    summary.expectedIPW[r]=ipwValid[r]?ipwMean[r]:null;
    summary.ipwBias[r]=ipwValid[r]?ipwMean[r]-truth[r]:null;
  }
  return {summary,config:cfg,worlds};
}
function runCandidate() {
  const scenarios=Object.keys(configs).map(k=>enumerate(k,configs[k]));
  return {allocation:"issue-8640-method-a02",n:N,horizon:H,
    assignment:"two within-pair fair coin assignments; one A and one B per pair",
    scenarios,scope:"finite synthetic identification method only; no historical/live inference"};
}
