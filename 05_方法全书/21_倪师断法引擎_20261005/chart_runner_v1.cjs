'use strict';
// 排盘器：只调用正式站快照（a908）的原模块，不重写任何排盘算法。
// 流程与网站一致：formToBirthInfo → setBrightnessSchool(默认) → generateChart → applyWenmoSchoolPatches(默认十项)。
// 用法：node chart_runner_v1.cjs < inputs.json > charts.json
//   inputs.json = [{"id": "...", "form": {calendarType, year, month, day, clockHour, clockMinute, gender, isLeapMonth, longitude, unknownTime}}]
// 环境：TZ=Asia/Taipei；当前时间冻结为 2026-10-01T04:00:00Z（与快照合成验收相同），只影响「当前年龄」类字段。
const fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto');
const Module = require('node:module');
const SNAP = path.resolve(__dirname, '../网站引擎快照/正式站只读快照_20261001_v1');
const SRC = path.join(SNAP, 'source');
const ENTRY = ['lib/ziwei/share.ts', 'lib/ziwei/date-utils.ts', 'lib/ziwei/algorithm.ts', 'lib/ziwei/wenmo-config.ts',
  'lib/ziwei/wenmo-patches.ts', 'lib/ziwei/constants.ts'];
const hash = b => crypto.createHash('sha256').update(b).digest('hex');
const ts = require(path.join(SRC, 'node_modules/typescript/lib/typescript.js'));
const loaded = [];
const nativeResolve = Module._resolveFilename;
Module._resolveFilename = function (request, parent, isMain, options) {
  if (request.startsWith('@/')) request = path.join(SRC, request.slice(2));
  const r = nativeResolve.call(this, request, parent, isMain, options);
  if (!r.startsWith(SRC + path.sep) && !Module.builtinModules.includes(request.replace(/^node:/, ''))) throw new Error('resolution outside snapshot: ' + r);
  return r;
};
for (const ext of ['.ts', '.tsx']) Module._extensions[ext] = function (module, filename) {
  const raw = fs.readFileSync(filename);
  loaded.push({path: path.relative(SRC, filename), sha256: hash(raw)});
  const out = ts.transpileModule(raw.toString('utf8'), {fileName: filename, compilerOptions: {target: ts.ScriptTarget.ES2017,
    module: ts.ModuleKind.CommonJS, esModuleInterop: true, jsx: ts.JsxEmit.React, sourceMap: false}});
  module._compile(out.outputText, filename);
};
const RealDate = global.Date, frozen = RealDate.parse('2026-10-01T04:00:00.000Z');
function FixedDate(...a) { if (new.target) return Reflect.construct(RealDate, a.length ? a : [frozen], new.target); return new RealDate(frozen).toString(); }
Object.setPrototypeOf(FixedDate, RealDate); FixedDate.prototype = RealDate.prototype; FixedDate.now = () => frozen; global.Date = FixedDate;
const ex = Object.assign({}, ...ENTRY.map(rel => require(path.join(SRC, rel))));
const defaults = ex.WENMO_DEFAULT_CONFIG;
const inputs = JSON.parse(fs.readFileSync(0, 'utf8'));
const rows = [];
for (const c of inputs) {
  try {
    const form = Object.assign({calendarType: 'solar', isLeapMonth: false, longitude: 120, unknownTime: false, city: '', province: '', name: ''}, c.form);
    for (const k of ['year', 'month', 'day', 'clockHour', 'clockMinute']) form[k] = String(form[k]);
    const birth = ex.formToBirthInfo(form, {lateZishi: defaults.lateZishi});
    ex.setBrightnessSchool(defaults.brightnessSchool);
    const chart = ex.generateChart(birth, {leapMonth: defaults.leapMonth});
    ex.applyWenmoSchoolPatches(chart, structuredClone(defaults));
    rows.push({id: c.id, form, birth, chart});
  } catch (e) { rows.push({id: c.id, error: String(e && e.stack || e)}); }
}
global.Date = RealDate;
process.stdout.write(JSON.stringify({schema: 'chart-runner-v1', engine_snapshot: 'a908a6924f0ba45a4ec2c9e815308d0985c90741',
  defaults, frozen_now: '2026-10-01T04:00:00.000Z', modules_loaded: loaded, rows}) + '\n');
