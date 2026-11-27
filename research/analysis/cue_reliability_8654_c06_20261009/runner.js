// Single-run orchestrator for Issue #8654 C06. Raw is committed before audit.
"use strict";
const {execFileSync}=require("child_process");
const crypto=require("crypto");
const repo="Unjuno/agent-interface";
const branch="research/8654-c06-stochastic-support-20261009";
const sourceFreezeHead="8f13efb2597fc9c3fff0f68d73d37edbf9dcbc28";
const expectedCandidateSha="d544618f50375b26b0415219e753ba96179916462fbbf2df4bad2f17c335c5df";
const expectedAuditorSha="f95a859a6ed5be222a32670b78a5636ebb67dcb3d11a048785fb6cd6a80e64f0";
const base="research/analysis/cue_reliability_8654_c06_20261009/";
function gh(args,input) {
  const opts={encoding:"utf8",maxBuffer:32*1024*1024};
  const out=input===undefined?execFileSync("gh",["api",...args],opts):execFileSync("gh",["api",...args,"--input","-"],{...opts,input:JSON.stringify(input)});
  return JSON.parse(out);
}
function sha(s){return crypto.createHash("sha256").update(s,"utf8").digest("hex");}
function getFile(path) {
  const x=gh(["repos/"+repo+"/contents/"+path+"?ref="+branch]);
  return {sha:x.sha,text:Buffer.from(x.content,"base64").toString("utf8")};
}
function commitBatch(files,message,expectedHead) {
  const ref=gh(["repos/"+repo+"/git/ref/heads/"+branch]);
  if(ref.object.sha!==expectedHead) throw Error("branch head changed: "+ref.object.sha);
  const commit=gh(["repos/"+repo+"/git/commits/"+expectedHead]);
  const tree=[];
  for(const [path,content] of Object.entries(files).sort(([a],[b])=>a.localeCompare(b))) {
    const blob=gh(["repos/"+repo+"/git/blobs","--method","POST"],{content,encoding:"utf-8"});
    tree.push({path,mode:"100644",type:"blob",sha:blob.sha});
  }
  const newTree=gh(["repos/"+repo+"/git/trees","--method","POST"],{base_tree:commit.tree.sha,tree});
  const next=gh(["repos/"+repo+"/git/commits","--method","POST"],{message,tree:newTree.sha,parents:[expectedHead]});
  const moved=gh(["repos/"+repo+"/git/refs/heads/"+branch,"--method","PATCH"],{sha:next.sha,force:false});
  if(moved.object.sha!==next.sha) throw Error("ref update mismatch");
  return next.sha;
}
function main() {
  const claimedRunnerSha=process.argv[1]||"";
  const freezeRef=gh(["repos/"+repo+"/git/ref/heads/"+branch]);
  const runnerFreezeHead=freezeRef.object.sha;
  if(runnerFreezeHead===sourceFreezeHead) throw Error("runner is not frozen on branch");
  const runnerFile=getFile(base+"runner.js");
  if(sha(runnerFile.text)!==claimedRunnerSha) throw Error("runner source hash mismatch");
  const candidateFile=getFile(base+"candidate.js"), auditorFile=getFile(base+"audit.js");
  const candidateSrc=candidateFile.text, auditSrc=auditorFile.text;
  const candidateSha=sha(candidateSrc), auditorSha=sha(auditSrc);
  if(candidateSha!==expectedCandidateSha||auditorSha!==expectedAuditorSha) throw Error("frozen source hash mismatch");
  const enumerate=new Function(candidateSrc+"\nreturn enumerateC06;")();
  const t0=process.hrtime.bigint();
  const generated=enumerate();
  const generationMs=Number(process.hrtime.bigint()-t0)/1e6;
  const raw=generated.files;
  const rawEntries=Object.entries(raw).sort(([a],[b])=>a.localeCompare(b));
  const fileManifest=rawEntries.map(([path,content])=>({path,bytes:Buffer.byteLength(content),sha256:sha(content),rows:content.trimEnd().split("\n").length}));
  const totalRows=fileManifest.reduce((s,x)=>s+x.rows,0);
  const manifest={allocation:"C06",issue:8654,raw_committed_before_audit:true,source_freeze_head:sourceFreezeHead,runner_freeze_head:runnerFreezeHead,
    candidate_sha256:candidateSha,auditor_sha256:auditorSha,denominator:generated.denominator,
    rows:totalRows,files:fileManifest,execution:{node:process.version,platform:process.platform,arch:process.arch,
      runner_sha256:claimedRunnerSha,generation_ms:generationMs}};
  const rawCommit=commitBatch({...raw,[base+"RAW_MANIFEST.json"]:JSON.stringify(manifest,null,2)+"\n"},
    "research(#8654): custody C06 raw enumeration before audit",runnerFreezeHead);
  const postRawRef=gh(["repos/"+repo+"/git/ref/heads/"+branch]);
  if(postRawRef.object.sha!==rawCommit) throw Error("raw commit not at branch head");
  const auditFn=new Function(auditSrc+"\nreturn auditC06;")();
  const auditStart=process.hrtime.bigint();
  let summary=null, auditError=null;
  try { summary=auditFn(raw); } catch(e) { auditError=String(e&&e.stack||e); }
  const auditMs=Number(process.hrtime.bigint()-auditStart)/1e6;
  const gate=!!summary && summary.rows===197376 && summary.unique===197376 &&
    summary.mutations_rejected===4 && summary.exact_known_propensity_expectation===true &&
    summary.greedy_unidentifiable_rows===768 && Object.values(summary.groups).every(x=>x==="unit_mass");
  const status=gate?"PASS_METHOD_SCOPED":"FAIL_METHOD";
  const auditRecord={allocation:"C06",status,raw_commit:rawCommit,source_freeze_head:sourceFreezeHead,runner_freeze_head:runnerFreezeHead,
    candidate_sha256:candidateSha,auditor_sha256:auditorSha,raw_manifest:base+"RAW_MANIFEST.json",
    audit_invocations:1,audit_ms: auditMs,summary,error:auditError,
    limits:["finite synthetic one-step design","no GUI/model/user/runtime/safety/task-benefit claim"]};
  const report="# Issue #8654 C06 — stochastic partial-feedback enumeration\n\n"+
    "Disposition: "+status+". Candidate and audit sources were frozen at source commit " +sourceFreezeHead+".\n\n"+
    "Candidate enumerated "+totalRows+" joint action/reward histories across three regimes. Raw JSONL shards and their hash manifest were committed at "+rawCommit+" before the independent auditor ran.\n\n"+
    "Audit summary:\n\n"+JSON.stringify(summary,null,2)+"\n\n"+
    (auditError?"Audit error: "+auditError.replace(/\n/g," ")+"\n\n":"")+
    "The design is exact for Bernoulli potential outcomes with four trials per context. Diagnostic action probability is 1/4 for the cue-opposed action and 3/4 for the cue-aligned action; greedy support is intentionally deficient. This is method evidence only, not evidence that exploration improves real-agent behavior or is safe in a GUI.\n";
  const finalHead=commitBatch({
    [base+"AUDIT.json"]:JSON.stringify(auditRecord,null,2)+"\n",
    [base+"REPORT.md"]:report,
    [base+"RUN.json"]:JSON.stringify({allocation:"C06",candidate_invocations:1,audit_invocations:1,
      raw_commit:rawCommit,final_status:status,main_base:"2a0016575c105a04ccd972920329c291b86d7d0b",
      source_freeze_head:sourceFreezeHead,runner_freeze_head:runnerFreezeHead,
      branch,runner_sha256:claimedRunnerSha,execution_environment:"local Node process; no container, WSLc, Docker, GUI or model"},null,2)+"\n"
  },"research(#8654): retain C06 independent audit",rawCommit);
  process.stdout.write(JSON.stringify({status,totalRows,rawCommit,finalHead,candidateSha,auditorSha,
    runnerSha256:claimedRunnerSha,generationMs,auditMs,summary,error:auditError})+"\n");
}
main();
