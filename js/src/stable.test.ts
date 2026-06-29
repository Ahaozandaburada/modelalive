import assert from "node:assert/strict";
import {
  compareFingerprints,
  fingerprintFromResponses,
  listStablePrompts,
  responseDistance,
} from "./stable.js";

assert.ok(listStablePrompts().length >= 5);
assert.equal(responseDistance("hello world", "hello world"), 0);
assert.ok(responseDistance("hello world", "goodbye moon") > 0.2);

const responses = Object.fromEntries(listStablePrompts().map((p) => [p.id, ["fixture-response"]]));
const base = fingerprintFromResponses("gpt-4o", responses);
const same = fingerprintFromResponses("gpt-4o", responses);
const report = compareFingerprints(base, same, 0.25);
assert.equal(report.stable, true);

const shifted = { ...responses, math_fixed: ["999999"] };
const drift = compareFingerprints(base, fingerprintFromResponses("gpt-4o", shifted), 0.01);
assert.equal(drift.stable, false);

console.log("stable.test.ts ok");
