from pathlib import Path
import shutil,difflib
source=Path('app-original');target=Path('app-patched')
shutil.copytree(source,target,dirs_exist_ok=True)
p=target/'nma-inconsistency/index.html';s=p.read_text(encoding='utf-8');original=s
a=s.index('    function parse(text) {');b=s.index('    // --- math utils',a)
s=s[:a]+'''    function parse(text) {
      // Preserve quoted treatment/study labels and optional study identifiers.
      const records = []; let row = [], field = "", quoted = false;
      for (let i = 0; i <= text.length; i++) {
        const c = i === text.length ? "\\n" : text[i];
        if (c === '"') {
          if (quoted && text[i + 1] === '"') { field += '"'; i++; }
          else quoted = !quoted;
        } else if (!quoted && (c === ',' || c === '\\n')) {
          row.push(field.trim()); field = "";
          if (c === '\\n') { records.push(row); row = []; }
        } else if (c !== '\\r' || quoted) field += c;
      }
      if (quoted) return [];
      return records.map((parts, i) => {
        const te = Number(parts[2]), se = Number(parts[3]);
        if (!parts[0] || !parts[1] || parts[0] === parts[1] ||
            !parts[2] || !Number.isFinite(te) || !Number.isFinite(se) || se <= 0) return null;
        return { A: parts[0], B: parts[1], te, se, study: parts[4] || `row_${i + 1}` };
      }).filter(Boolean);
    }
    function escapeMarkup(value) {
      return String(value).replace(/&/g, "&amp;").replace(/</g, "&lt;")
        .replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
    }
    function refuse(reason) {
      _lastInco = { status: "refused", reason };
      document.getElementById("ns-body").innerHTML = "";
      document.getElementById("ns-plot").innerHTML = "";
      document.getElementById("dbt").textContent = reason;
    }
    function inputIssue(rows) {
      if (rows.length < 3) return "At least 3 valid contrasts are required.";
      const studies = new Map();
      for (const r of rows) {
        if (!studies.has(r.study)) studies.set(r.study, []);
        studies.get(r.study).push(r);
      }
      for (const group of studies.values()) {
        if (new Set(group.flatMap(r => [r.A, r.B])).size > 2)
          return "Multi-arm studies are unsupported: correlated contrasts require study covariance.";
      }
      if ([...studies.values()].some(group => group.length > 1))
        return "Repeated study IDs are unsupported: enter one independent contrast per study.";
      const all = new Set(rows.flatMap(r => [r.A, r.B]));
      const seen = new Set([rows[0].A]);
      for (let old = -1; old !== seen.size;) {
        old = seen.size;
        for (const r of rows) if (seen.has(r.A) || seen.has(r.B)) { seen.add(r.A); seen.add(r.B); }
      }
      if (seen.size !== all.size) return "The treatment network is disconnected.";
      return null;
    }

'''+s[b:]
s=s.replace('function pz(z) { return 2 * (1 - pnorm(Math.abs(z))); }','function pz(z) { return 1 - chiSqCDF(z * z, 1); }')
s=s.replace('for (let i = 0; i < 60; i++) {','for (let i = 0; i < 100; i++) {').replace('if (hi - lo < 1e-10) break;','if (hi - lo < 1e-13 * Math.max(1, mid)) break;')
s=s.replace('[r.A, r.B].sort().join("|")','JSON.stringify([r.A, r.B].sort())').replace('const [a, b] = key.split("|");','const [a, b] = JSON.parse(key);')
s=s.replace('if (direct.length === 0 || others.length === 0) continue;', '''if (direct.length === 0 || others.length === 0) continue;
        // Check graph connectivity before solving: floating-point elimination
        // can invert a disconnected Laplacian with a tiny nonzero pivot.
        const reachable = new Set([a]);
        for (let old = -1; old !== reachable.size;) {
          old = reachable.size;
          for (const r of others) if (reachable.has(r.A) || reachable.has(r.B)) {
            reachable.add(r.A); reachable.add(r.B);
          }
        }
        if (!reachable.has(b)) continue;''')
s=s.replace('return { Q: cons.Q, df: cons.df, p: NaN, note: "inconsistency model unidentifiable (designs ≤ basic parameters)" };','return { Q: 0, df: 0, p: NaN, note: "No closed loops: inconsistency is not testable." };')
s=s.replace('const dQ = Math.max(0, cons.Q - Qfull);','// Nested weighted projections: avoid cancellation of large residual sums.\n        const dQ = y.reduce((sum, _, i) => sum + w[i] * (fit_[i] - cons.X[i].reduce((v, x, j) => v + x * cons.beta[j], 0)) ** 2, 0);')
s=s.replace('if (rows.length < 3) return;','const issue = inputIssue(rows);\n      if (issue) { refuse(issue); return; }')
s=s.replace('const tau2 = estimateTau2(rows, method);','let tau2;\n      try { tau2 = estimateTau2(rows, method); fitNMA(rows, undefined, tau2); }\n      catch (_) { refuse("Network fit is singular or numerically invalid."); return; }')
s=s.replace('${r.comparison}', '${escapeMarkup(r.comparison)}')
s=s.replace('${g.p < 0.05 ? "evidence of inconsistency" : "no evidence of inconsistency"}', '${!Number.isFinite(g.p) ? "inconsistency is not testable" : g.p < 0.05 ? "evidence of inconsistency" : "no evidence of inconsistency"}')
s=s.replace('const estimates = {};','const estimates = Object.create(null);').replace('const estimatesRandom = {};','const estimatesRandom = Object.create(null);')
s=s.replace('} catch (_) { /* leave _lastInco as-is on degenerate input */ }','} catch (_) { refuse("Network fit is singular or numerically invalid."); }')
s=s.replace('dbt: { Q: g.Q, df: g.df, p: g.p },','dbt: { Q: g.Q, df: g.df, p: Number.isFinite(g.p) ? g.p : null },')
s=s.replace('const allMeans = ns.flatMap(r => [r.direct.mean, r.indirect.mean]);\n      const lo = Math.min(0, ...allMeans) - 0.3, hi = Math.max(0, ...allMeans) + 0.3;', 'const allLimits = ns.flatMap(r => [r.direct.mean - Z975 * r.direct.se, r.direct.mean + Z975 * r.direct.se, r.indirect.mean - Z975 * r.indirect.se, r.indirect.mean + Z975 * r.indirect.se]);\n      const lo = Math.min(0, ...allLimits) - 0.3, hi = Math.max(0, ...allLimits) + 0.3;')
s=s.replace('<code>A, B, effect, SE</code>','<code>A, B, effect, SE[, study ID]</code>')
s=s.replace('Multiple rows per comparison allowed.','Independent two-arm studies only. Multiple rows per comparison allowed. Supply study IDs to detect repeated or multi-arm studies; correlated contrasts are unsupported.')
s=s.replace('var rows = MaComparisons.toContrasts(env);','if (env.studies.some(function (s) { return Array.isArray(s.arms) && s.arms.length > 2; })) { refuse("Multi-arm studies are unsupported: correlated contrasts require study covariance."); return; }\n      var rows = MaComparisons.toContrasts(env);')
s=s.replace('notify("Shared network bus is empty."); return;', 'refuse("Shared network bus is empty."); notify("Shared network bus is empty."); return;')
s=s.replace('if (!rows.length) { notify(', 'if (!rows.length) { refuse("The shared network has no supported contrasts."); notify(')
s=s.replace('ta.value = rows.map(function (r) { return r.treatment1 + ", " + r.treatment2 + ", " + r.te + ", " + r.se; }).join("\\n");','function csv(v) { return \'"\' + String(v).replace(/"/g, \'""\') + \'"\'; }\n      ta.value = rows.map(function (r) { return [r.treatment1, r.treatment2, r.te, r.se, r.study].map(csv).join(","); }).join("\\n");')
s=s.replace('RE models pool heterogeneity across designs (shared τ²) before testing inconsistency', 'RE models estimate shared τ² from consistency-model residuals before testing inconsistency')
s=s.replace('and a global design-by-treatment test (Higgins et al. 2012).','and a global design-by-treatment test (Higgins et al. 2012), restricted to independent two-arm studies.')
s=s.replace('to ≤1e-8 via', 'using')
s=s.replace('Node-splitting: Dias S et al.', 'For independent two-arm studies, removing each direct comparison gives the same split as netmeta back-calculation / SIDE at a fixed shared τ². RE global Q uses this consistency-model τ² as a preset; it is not the default within-design τ² test from decomp.design. Node-splitting: Dias S et al.')
p.write_text(s,encoding='utf-8',newline='\n')
readme=target/'nma-inconsistency/README.md';r=readme.read_text(encoding='utf-8');r=r.replace('multi-arm trials in NMA shape — multiple rows per study, one per arm.','independent two-arm contrast rows: A, B, effect, SE, optional study ID. Multi-arm studies are refused because covariance is unsupported.');r=r.replace('Receipts and JSON exports include `producedBy` (app version, git SHA, build timestamp) — see `shared/build-info.js`.','This page exports its numerical result state as JSON, CSV and Markdown. Record the source checkout commit separately; the shared `build-info.js` identity is not attached to this page’s result exports.');readme.write_text(r,encoding='utf-8',newline='\n')
diff=''
for rel in ['nma-inconsistency/index.html','nma-inconsistency/README.md']:
 diff+=''.join(difflib.unified_diff((source/rel).read_text(encoding='utf-8').splitlines(True),(target/rel).read_text(encoding='utf-8').splitlines(True),fromfile='a/'+rel,tofile='b/'+rel))
Path('fix.patch').write_text(diff,encoding='utf-8',newline='\n')
print('App-only patch written; upstream untouched')
