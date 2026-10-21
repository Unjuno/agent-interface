#!/usr/bin/env node
// Issue #8654 C05: exact finite enumeration of propensity misspecification.
"use strict";
const regimes = ["STABLE", "REVERSAL", "GLOBAL_SHIFT"];
const pref = c => c;
const good = [1, 1, 0, 1], bad = [0, 0, 1, 0];
function reward(regime, c, a, t) {
  const aligned = a === pref(c);
  let v = aligned ? good[t] : bad[t];
  if (regime === "REVERSAL") v = aligned ? bad[t] : good[t];
  if (regime === "GLOBAL_SHIFT") v = Math.max(0, v - 0.5);
  return v;
}
function oracle(regime) {
  const out = [];
  for (let c=0;c<2;c++) for (let a=0;a<2;a++) for (let t=0;t<4;t++)
    out.push({c,a,t,y:reward(regime,c,a,t)});
  return out;
}
function score(regime, policy, mask) {
  const rows=[]; let prob=1, bit=0;
  for (let c=0;c<2;c++) for (let t=0;t<4;t++,bit++) {
    const flip=policy==="DIAGNOSTIC" ? ((mask>>bit)&1) : 0;
    const a=flip ? 1-pref(c) : pref(c);
    const mu=policy==="DIAGNOSTIC" ? (flip ? 0.25 : 0.75) : 1;
    prob *= policy==="DIAGNOSTIC" ? (flip ? 0.25 : 0.75) : 1;
    rows.push({c,a,t,y:reward(regime,c,a,t),mu,reported_mu:policy==="DIAGNOSTIC"?0.5:1});
  }
  const cells=new Set(rows.map(x=>x.c+":"+x.a));
  const identified=cells.size===4;
  const target=oracle(regime).reduce((s,x)=>s+x.y,0)/16;
  const factual=rows.reduce((s,x)=>s+x.y,0)/8;
  // HT diagnostic values are retained for exact design-expectation audit only.
  const ht=rows.reduce((s,x)=>s+0.5*x.y/x.mu,0)/8;
  const misspec=rows.reduce((s,x)=>s+0.5*x.y/x.reported_mu,0)/8;
  const learner_rows=rows.map(({c,a,t,y,mu})=>({c,a,t,y,mu}));
  return {id:regime+"|"+policy+"|"+mask,regime,policy,mask,prob,
    rows,oracle:oracle(regime),target,factual,ht,misspec,
    decision:identified?"IDENTIFIED":"UNIDENTIFIABLE",
    reported_estimate:identified?ht:null,
    learner_rows};
}
const all=[];
for(const r of regimes) {
  all.push(score(r,"GREEDY",0));
  for(let m=0;m<256;m++) all.push(score(r,"DIAGNOSTIC",m));
}
process.stdout.write(all.map(x=>JSON.stringify(x)).join("\n")+"\n");
