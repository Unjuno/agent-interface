#!/usr/bin/env node
const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");
const audit = require("./audit.js");
const root = process.argv[2] || ".";
const specs = [
  { id: "v38", dir: "research/doom/results/map01-v38-integrated-threat-live-01", hashes: { "report.json": "d96b9032c7f55645dde20a1f95d916c943713914", "runtime/events.jsonl": "02d65d49b61feadbdec2e051bd23d1ca845d5df1", "planner-protocol.jsonl": "48bc97f10507475df287d6e4c70358dfce52733f" } },
  { id: "v39", dir: "research/doom/results/map01-v39-coast-liveness-live-01", hashes: { "report.json": "bff2459036dcdcc44ed100b0c0bc657e1bb8e69a", "runtime/events.jsonl": "cbaeed9c7ba27b53cef9d10730ae33313371ad9a", "planner-protocol.jsonl": "c67e5c0fcefb8b1a3d690ae980f9ea25c45f6b23" } }
];
function gitBlobSha(bytes) { return crypto.createHash("sha1").update(Buffer.concat([Buffer.from("blob " + bytes.length + "\0"), bytes])).digest("hex"); }
const runs = specs.map((spec) => {
  const read = (relative) => {
    const bytes = fs.readFileSync(path.join(root, spec.dir, relative));
    if (gitBlobSha(bytes) !== spec.hashes[relative]) throw new Error(spec.id + " blob SHA mismatch: " + relative);
    return bytes.toString("utf8");
  };
  return { id: spec.id, reportText: read("report.json"), eventsText: read("runtime/events.jsonl"), protocolText: read("planner-protocol.jsonl") };
});
process.stdout.write(JSON.stringify(audit(runs), null, 2) + "\n");
