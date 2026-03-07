import process from "node:process";
import { performance } from "node:perf_hooks";

import { initTokenizer } from "../src/index.js";

const DEFAULT_SCENARIOS = [
  "hello world",
  "line1\\nline2",
  "ASCII symbols !@#$%^&*()[]{}",
  "Cafe\u0301",
  "naive facade cooperate",
  "emoji 🙂🚀🔥",
  "math alpha beta gamma",
  "tabs\\tand spaces",
  "mixed accents: deja vu",
  "quotes 'single' and \"double\"",
];

async function readStdin() {
  const chunks = [];
  for await (const chunk of process.stdin) {
    chunks.push(chunk);
  }
  return Buffer.concat(chunks).toString("utf8").trim();
}

function toScenarios(payload) {
  if (!payload) {
    return DEFAULT_SCENARIOS;
  }
  const parsed = JSON.parse(payload);
  const candidate = Array.isArray(parsed) ? parsed : parsed.scenarios;
  if (!Array.isArray(candidate) || candidate.length === 0) {
    throw new Error("stdin JSON must contain a non-empty scenarios array");
  }
  for (let i = 0; i < candidate.length; i += 1) {
    if (typeof candidate[i] !== "string") {
      throw new Error(`scenarios[${i}] must be string`);
    }
  }
  return candidate;
}

const tokenizer = await initTokenizer();
const payload = await readStdin();
const scenarios = toScenarios(payload);

const results = scenarios.map((text) => {
  const t0 = performance.now();
  const ids = tokenizer.encode(text);
  const t1 = performance.now();
  const decoded = tokenizer.decode(ids);
  const t2 = performance.now();
  return {
    text,
    ids,
    decoded,
    token_count: ids.length,
    encode_ms: Number((t1 - t0).toFixed(6)),
    decode_ms: Number((t2 - t1).toFixed(6)),
    roundtrip_match: decoded === text.normalize("NFC"),
  };
});

const mismatch_count = results.filter((item) => !item.roundtrip_match).length;

const output = {
  module_version: tokenizer.version,
  scenario_count: scenarios.length,
  mismatch_count,
  results,
};

process.stdout.write(`${JSON.stringify(output)}\n`);
if (mismatch_count > 0) {
  process.exitCode = 1;
}
