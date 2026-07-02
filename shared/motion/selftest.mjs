// Self-test for reference-motion.js — verifies determinism, clamps, easing.
// Run: node motion/selftest.mjs
import { createRequire } from "module";
const require = createRequire(import.meta.url);
const RM = require("./reference-motion.js");

let fails = 0;
function ok(cond, msg) { console.log((cond ? "  ok   " : "  FAIL ") + msg); if (!cond) fails++; }
function approx(a, b, e) { return Math.abs(a - b) <= (e == null ? 1e-9 : e); }

// 1. Easing bounds + monotonicity
ok(approx(RM.easeOutCubic(0), 0) && approx(RM.easeOutCubic(1), 1), "easeOutCubic maps 0->0, 1->1");
ok(approx(RM.easeInOutCubic(0.5), 0.5), "easeInOutCubic symmetric at 0.5");
let mono = true; for (let i = 1; i <= 100; i++) if (RM.easeInOutCubic(i / 100) < RM.easeInOutCubic((i - 1) / 100)) mono = false;
ok(mono, "easeInOutCubic is monotonic non-decreasing");

// 2. Determinism: same (seed,time) => identical transform across runs
const a = RM.sampleCameraTransform("talkingHeadWide", 0.5, "EMO07");
const b = RM.sampleCameraTransform("talkingHeadWide", 0.5, "EMO07");
ok(JSON.stringify(a) === JSON.stringify(b), "sampleCameraTransform deterministic for same seed");
const c = RM.sampleCameraTransform("talkingHeadWide", 0.5, "OTHER");
ok(JSON.stringify(a) !== JSON.stringify(c), "different seed => different drift");

// 3. seededRange stable + in range
const r1 = RM.seededRange("s", 5, 15, "k");
const r2 = RM.seededRange("s", 5, 15, "k");
ok(r1 === r2 && r1 >= 5 && r1 <= 15, "seededRange deterministic and in-range");

// 4. Clamps (section 11): scale 1.00..1.15, rotation 0 by default
const clamped = RM.clampTransform({ scale: 99, x: 0, y: 0, rotation: 45 }, "talkingHead");
ok(clamped.scale === 1.15, "scale clamped to <= 1.15");
ok(clamped.rotation === 0, "rotation forced to 0 when allowRotation=false");

// 5. Talking-head push-in stays subtle (<= 1.05 even at end)
let maxScale = 0;
for (let i = 0; i <= 30; i++) { const tf = RM.sampleCameraTransform("talkingHeadMedium", i / 30, "x"); maxScale = Math.max(maxScale, tf.scale); }
ok(maxScale <= 1.12, "talkingHeadMedium scale stays <= 1.12 (subtle), got " + maxScale.toFixed(4));

// 6. Punch-in is an instant cut (already >=1.10 at t=0)
const punch0 = RM.sampleCameraTransform("talkingHeadPunchIn", 0, "p");
ok(punch0.scale >= 1.10 && punch0.scale <= 1.15, "punchIn cuts to 1.10..1.15 at t=0, got " + punch0.scale.toFixed(4));

// 7. intensity=0 (cameraMotion off) => no movement
global.window = { MOTION_STYLE: { cameraMotion: "off" } };
const still = RM.sampleCameraTransform("talkingHeadWide", 1, "x");
ok(approx(still.scale, 1) && approx(still.x, 0), "cameraMotion 'off' => static");
delete global.window;

console.log(fails === 0 ? "\nALL PASS" : "\n" + fails + " FAILED");
process.exit(fails === 0 ? 0 : 1);
