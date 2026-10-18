#!/usr/bin/env node
// Independent raw-only audit for Issue #8654 C05. Reads JSONL on stdin.
"use strict";
const fs=require("fs");
const text=fs.readFileSync(0,"utf8").trim();
const data=text.split(/\r?\n/).map(JSON.parse);
const regimes=["STABLE","REVERSAL","GLOBAL_SHIFT"];
const pref=c=>c, good=[1,1,0,1], bad=[0,0,1,0];
function y(r,c,a,t) {
 let v=(a===pref(c))?good[t]:bad[t];
 if(r==="REVERSAL") v=(a===pref(c))?bad[t]:good[t];
 if(r==="GLOBAL_SHIFT") v=Math.max(0,v-0.5);
 return v;
}
function close(a,b){return Math.abs(a-b)<1e-12;}
function audit(rows) {
 if(rows.length!==771) throw Error("row_count");
 const seen=new Set(), mass={};
 for(const x of rows) {
  if(seen.has(x.id)) throw Error("duplicate_id"); seen.add(x.id);
  if(!regimes.includes(x.regime)) throw Error("regime");
  const expectedMask=x.policy==="GREEDY"?[0]:Array.from({length:256},(_,i)=>i);
  if(!expectedMask.includes(x.mask)) throw Error("mask");
  const bits=x.policy==="DIAGNOSTIC"?x.mask:0;
  let p=1, cells=new Set(), factual=0, ht=0, miss=0;
  if(x.rows.length!==8 || x.oracle.length!==16 || x.learner_rows.length!==8) throw Error("shape");
  for(let i=0;i<8;i++) {
   const q=x.rows[i], c=Math.floor(i/4), t=i%4, flip=(bits>>i)&1;
   const a=flip?1-pref(c):pref(c), mu=x.policy==="DIAGNOSTIC"?(flip?0.25:0.75):1;
   if(q.c!==c||q.t!==t||q.a!==a||!close(q.y,y(x.regime,c,a,t))||!close(q.mu,mu)) throw Error("factual_row");
   if(!close(q.reported_mu,x.policy==="DIAGNOSTIC"?0.5:1)) throw Error("logged_misspec");
   const l=x.learner_rows[i];
   if(JSON.stringify(l)!==JSON.stringify({c,a,t,y:q.y,mu:q.mu})) throw Error("learner_input_leak_or_mismatch");
   p*=x.policy==="DIAGNOSTIC"?(flip?0.25:0.75):1;
   cells.add(c+":"+a); factual+=q.y; ht+=0.5*q.y/q.mu; miss+=0.5*q.y/q.reported_mu;
  }
  const target=x.oracle.reduce((s,q)=>s+q.y,0)/16;
  for(let i=0;i<16;i++) {const c=Math.floor(i/8),a=Math.floor(i/4)%2,t=i%4,q=x.oracle[i];
   if(q.c!==c||q.a!==a||q.t!==t||!close(q.y,y(x.regime,c,a,t))) throw Error("oracle");
  }
  const identified=cells.size===4;
  if(!close(x.prob,p)||!close(x.target,target)||!close(x.factual,factual/8)||!close(x.ht,ht/8)||!close(x.misspec,miss/8)) throw Error("derived_metric");
  if(x.decision!==(identified?"IDENTIFIED":"UNIDENTIFIABLE")) throw Error("identifiability");
  if(x.reported_estimate!==(identified?x.ht:null)) throw Error("estimate_gate");
  mass[x.regime+"|"+x.policy]=(mass[x.regime+"|"+x.policy]||0)+x.prob;
 }
 for(const r of regimes) {
  if(!close(mass[r+"|GREEDY"],1)||!close(mass[r+"|DIAGNOSTIC"],1)) throw Error("probability_mass");
  const d=data.filter(x=>x.regime===r&&x.policy==="DIAGNOSTIC");
  if(!close(d.reduce((s,x)=>s+x.prob*x.ht,0),d[0].target)) throw Error("known_propensity_design_unbiasedness");
  if(!close(d.reduce((s,x)=>s+x.prob*x.misspec,0),d[0].target)) {
    // Misspecification may coincide in a particular regime; record, do not fail.
  }
 }
 if(data.filter(x=>x.policy==="GREEDY").some(x=>x.decision!=="UNIDENTIFIABLE")) throw Error("greedy_abstention");
 return {rows:data.length,unique_ids:seen.size,groups:Object.keys(mass).length,probability_mass:mass,
   known_propensity_exact_expectation:true,all_greedy_unidentifiable:true};
}
const result=audit(data);
const mutations=[
 d=>{d[1].rows[0].y=1-d[1].rows[0].y},
 d=>{d[1].rows[0].mu=0.5},
 d=>{d[1].decision="IDENTIFIED"},
 d=>{d[1].learner_rows[0].oracle_outcome=d[1].oracle[0].y}
];
let rejected=0;
for(const mutate of mutations){const copy=JSON.parse(JSON.stringify(data));mutate(copy);try{audit(copy)}catch{rejected++}}
if(rejected!==4) throw Error("mutation_controls");
process.stdout.write(JSON.stringify({...result,mutations_rejected:rejected})+"\n");
