# Plus browser tier re-run on the allmeta v1.8.0 bytes (21 Oct 2026)

This is the current browser evidence for the plus layer. `../browser/` is the earlier run on the pre-v1.8.0 bytes and is kept
as history (see `../browser/HISTORY.md`).

## Result

`pw-gates-v180.log`: **42 passed, 0 failed, 0 skipped** (Microsoft Edge 155.0.4283.62, Playwright 1.59.1, Node v24.13.0,
one worker). These are the same 42 tests and the same order as the archived `../browser/pw-gates6.log` (42 passed):

| Check | Archived run (`../browser/pw-gates6.log`) | v1.8.0 run (`pw-gates-v180.log`) |
|---|---|---|
| tests passed | 42/42 | 42/42 |
| in-page plus replay | 643413/643413 | 643413/643413 |
| tampered plus reference value | 643412/643413 (same first failure) | 643412/643413 (same first failure) |
| pinned base replay | 4627 checks, 122 configurations, 54 refusals | same test passes |
| live R (webR, netmeta 3.4-0, metafor 4.8-0), FE/DL/PM | pass | pass |
| walkthrough clicks (fresh load / example / own data / model) | 0 / 1 / paste only / 1 selection; total 3 | identical |
| axe, full page (WCAG 2.1 AA) | 0 violations, 29 passes | 0 violations, 29 passes |
| Figure 2 capture (`shots/fig2-capture.json`) | Edge 155.0.4283.62 | byte-identical JSON |
| usability test 23 | "invalid input explains and **keeps** results" | "invalid input explains and **clears** results" |
| walkthrough LOO sentence (PM, own data) | "Removing any single study leaves the global test on the same side of 0.05 ..." | "Among removals with a testable global p-value, the global test stays on the same side of 0.05 ..." |

The last two rows are the intended v1.8.0 behaviour, below. `expected-browser.json` records the expected values for this run
(all 42 test titles, the replay lines, the walkthrough record, and the superseded values). `analysis/verify_archive.py` checks
the log, the shots JSON and the record against each other. The screenshots (`shots/*.png`) are kept as evidence and are not
compared byte for byte: 7 of the 12 PNGs are byte-identical to the earlier run, and 5 differ (`fig2_D_loo_table`,
`walk-1`, `walk-3`, `walk-4`, `walk-5`). The text and state they show are checked through the JSON records and the tests.

## What changed in v1.8.0, and why

allmeta commit `1f5ce9e400762334c702b9e665ab0dcd0233c641` ("fix 3 P1 review findings"), merged into v1.8.0 by `d97ac74`
(Merge PR #160), fixed findings from the independent review of pull request #160. Exact change to `nma-inconsistency/plus-ui.js`
(`git diff e61378c 1cb3f84 -- nma-inconsistency/plus-ui.js`):

```diff
-        // Auto-run only input the page would accept; otherwise explain and keep results.
-        if (!window.inputIssue(window.parse(src.value)) && src.value !== shownText) window.run();
+        // Run refusals too, so the base result and observed plus/export state clear.
+        if (src.value !== shownText) window.run();
         else showInputMessage();
```

(plus the matching header comment: "a debounced edit to valid input" became "a debounced input edit").

Before, when the user typed input that the page would refuse, the panel explained the problem and kept the results of the
previous input on screen. The review found that this left stale results, plus panel output and exports that no longer
matched the input box. In v1.8.0 the debounced edit runs the page on invalid input too, so the page's own refusal clears the
base result, the plus panel and the export state, and the input message still explains the problem. The usability spec was
changed in the same commit to assert the new behaviour: status `refused`, no node-split rows, and an empty methods text.

The same commit changed `plus-core.js`: `globalFlip` is false unless both global p-values are finite, because losing the last
loop makes the test untestable, not a crossing. The stability sentence now begins "Among removals with a testable global
p-value". This is why the walkthrough sentence differs. The numbers in it are unchanged (global p 0.320 to 0.766).

## How it was run

The specs read the site root as `../../../` from `hub/shared/tests/`, as in the allmeta repository. A site was therefore
assembled with every file equal to its 1cb3f84 Git blob (`runner/site-manifest.json`, 49 files):

- 30 files from `plus/app/` (the panel, its validation assets and 5 test files) and 11 from `app/patched/`;
- 8 files that the page or the specs need but this archive does not carry, taken from allmeta 1cb3f84: the base parity, RE-parity
  and pinned-replay specs, their two oracle fixtures (`nma-inconsistency/tests/fixtures/`), `shared/alm-validate.js`,
  `shared/webr-runner.js`, and `favicon.ico`. Without the root `favicon.ico` the parity test "no console errors" fails on a
  404 (`favicon.ico` is requested by the browser, not by the page);
- `r-shiny/shinylive/webr/` (live R) was served read-only from an allmeta checkout whose Git tree for that path is
  `b62859ec7fe6415e5562ecca33387c8f018bcfc9`, the same tree as in 1cb3f84.

`runner/lane.config.mjs` is the allmeta `playwright.config.mjs` with one worker, the `msedge` channel, and `runner/serve.py` as the
static server on port 8088. The parity specs hard-code `http://localhost:8088`. Command, from the assembled `hub/shared/tests/`
with `@playwright/test` 1.59.1 and `@axe-core/playwright` installed:

```
P16_RUNNER=<this runner dir> ALLMETA_WEBR_DIR=<allmeta checkout>/r-shiny/shinylive/webr P16_SHOTS=<shots dir> \
  npx playwright test -c lane.config.mjs --workers=1 --reporter=line nma-inconsistency-parity.spec.mjs \
  nma-inconsistency-plus.spec.mjs nma-inconsistency-re-parity.spec.mjs nma-inconsistency-usability.spec.mjs \
  nma-inconsistency-walkthrough.spec.mjs validate-nma-inconsistency.spec.mjs
```

Two earlier attempts in the same session are not evidence. Each failed because of the runner, not the app: one used port 8417
(5 parity tests could not connect to localhost:8088), and one had no root `favicon.ico` (1 failure, a console 404). After both
fixes, the full set was run once more, unchanged, and that run is the log above. The archived `../browser/pw-a11y3.log`
(76-app portfolio a11y sweep) needs the whole allmeta portfolio and was not re-run.
