# Plus layer: the leave-one-study-out sensitivity panel (allmeta pull request #160)

`plus/app/` is a byte-exact copy (the committed git blobs) of `nma-inconsistency/` (without `nma-inconsistency/tests/`, the repository's
pre-existing unit tests and fixtures, which are not part of the panel) and the panel's browser specs at the head of
`feat/nma-inconsistency-plus` (commit and per-file SHA-256 in `plus/app/SOURCE.json`). The panel (`plus-core.js`, `plus-ui.js`)
calls the page's own engine functions and never re-implements them; see `plus/app/nma-inconsistency/validate/README-plus.md`.

Release re-pin: `plus/app/` now holds the allmeta v1.8.0 bytes (commit 1cb3f8409c7af75ed41f7e1811f9c502f900fc79). v1.8.0
changed `plus-core.js`, `plus-ui.js` and two tests (pull request #160 fixes). The Node replay below was re-run on these bytes
(643413/643413). The browser tier was re-run on these bytes: 42/42 passed (`evidence/browser-v180/`). In v1.8.0, invalid input
clears results (allmeta 1f5ce9e, the pull request #160 review fix). Before, it kept them. `evidence/browser/` is the earlier run, kept as
history; see `../RELEASE_EQUIVALENCE.md`.

## What is checked, and how to reproduce it

`validate.R` ends by sourcing `plus/validate-plus.R`, which

1. refuses unless R and package versions equal the recorded ones;
2. SHA-256-checks every app file against `plus/app/SOURCE.json` and every evidence file of the panel against `MANIFEST-plus.json`;
3. refits in native R (netmeta 3.7-0, metafor 5.2-1), with the archived oracle `validate/generate-plus.R`, a seeded subset of the
   153 configurations (every study removed in turn) and requires every quantity of every fresh refit to equal the archived
   reference `validate/plus/reference.json` within 1e-12 relative (strings, counts and statuses exact). The subset is every
   configuration with a refused removal, two loop configurations per model drawn with `set.seed(20261020)` and the first no-loop
   configuration per model. `PLUS_FULL=1` refits all 153 (about 7 hours). `PLUS_PLANT=1` plants a defect and the step must fail;
4. runs the panel's replay in Node.js against the pinned references (`validate/derive-plus-checks.cjs`) and requires
   `PLUS NODE REPLAY 643413/643413`.

## Recorded evidence (`plus/evidence/`)

- `r-oracle/`: the full reference was computed in three shards on two nodes. The 51 configurations computed on both were compared
  (`overlap2.log`: 45 identical apart from timing; 6 Paule-Mandel configurations differ by at most 2.08e-13). One shard on the
  first node ended with exit status 1 and no R error text while it was working on configuration 134 (which the second node
  completed); the six configurations it alone produced were refitted again in R: 6/6 identical in every leaf, maximum relative
  difference 0 (`recheck6-compare-byhand.log`).
- `node-replay/`: `PLUS NODE REPLAY 643413/643413` (leave-one-out 619,763; estimators 20,072; sentences 935; graph 2,643); with one
  reference tau-squared multiplied by 1 + 1e-6 (re-pinned in memory): 643412/643413 (`derive-tamper.log`).
- `browser-v180/`: the current browser evidence, the same 42 tests re-run on the v1.8.0 bytes (Edge 155.0.4283.62): 42/42
  passed, with "invalid input explains and clears results"; the expected values are in `expected-browser.json`.
- `browser/` (history, recorded before v1.8.0; `HISTORY.md`): Microsoft Edge 155, Playwright, one worker: the panel spec (in-page replay 643,413/643,413; value tamper caught; pin
  tampers refused; the 4,627-check base replay with the panel mounted), the usability and walkthrough specs (results without a
  click; real example 1 click; export 2; axe 0 violations), parity, re-parity and the base replay including live R.
- `r-scripts/`: the R script the panel exports (feature B). Rerun with the fixed generator (commit 5373102; one line per script changed: node-split names coerced with as.character, so fits without node-splits no longer stop) on one node with the panel's own runner `validate/run-scripts.ps1` (`run.log`): all 291 base scripts (one per analysed configuration) exited 0 with an N/N check line (11,415 quantities, `base-done.jsonl`); the 9 seeded leave-one-out scripts likewise (24,885 quantities, `loo-done.jsonl`); the planted script (first base script with its reference global Q scaled by 1.001) printed 68/69 and exited 1 (`planted.log`). Before the fix, 147 of the 291 base scripts (the fits without node-splits) stopped with an R error.

## Limits

The panel inherits the page's scope: independent two-arm contrasts; multi-arm studies are refused. Removal flags are descriptive
(no multiplicity adjustment). Browsers other than Edge 155 were not tested. The Node.js harness `validate-nma-inconsistency.node.cjs`
reports 4,437/4,627 on allmeta main because of a pre-existing linkedom contract drift; the browser replay (4,627/4,627) is the gate.

## Fresh validation (`plus/results/fresh-validate-731b379/`)

`Rscript validate.R` on a `git archive` copy of commit 731b379 on a second machine (R 4.6.0, netmeta 3.7.0, metafor 5.2.1; 3 h 9 min): original 79869/83592 and patched 76601/76601 (both match `expected/paper_values.json`), focused 194/319 and 319/319; plus layer: version and SHA-256 checks PASS, seeded native-R refit of 12 configurations / 173 drop-fits, 18414/18414 reference quantities reproduced (max relative difference 9.78e-14), `PLUS NODE REPLAY 643413/643413`; then `verify_archive.py` ARCHIVE PASS and `test_safeguards.py` SAFEGUARDS PASS (the R version test skipped: Rscript not on PATH for Python). `PLUS_PLANT=1` on a second clean copy: 18413/18414, the planted full Q of netmeta::Dogliotti2014::stroke::OR::two-arm-only::FE, and exit 1 (`plant-clean.log`). A first `PLUS_PLANT=1` run in the already-used copy stopped at the stale-result guard instead (`plant-stale-guard.log`); it is kept because it failed for the wrong reason and so does not count as the planted-defect test.
