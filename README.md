# Node-splitting and design-by-treatment inconsistency in the browser: validation against the R package netmeta

Current source: **allmeta v1.8.0**, tag `v1.8.0`, commit `1cb3f8409c7af75ed41f7e1811f9c502f900fc79`, DOI 10.5281/zenodo.23515177 (https://github.com/mahmood726-cyber/allmeta/releases/tag/v1.8.0), in `app/patched`. All 13 primary snapshot files and all 30 included `plus/app` files are the exact committed v1.8.0 bytes (Git blob ids recorded and checked). The archive was first re-cut against candidate `e61378ce260911af311fc45a3f91e239f15f7c5b`; v1.8.0 changed two primary files (export-bar CSS, build stamp) and four plus files (pull request #160 fixes to `plus-core.js` and `plus-ui.js` and their tests), and these were re-pinned to the v1.8.0 bytes. Provenance and pins: `app/candidate-source.json`, `plus/app/SOURCE.json`; equivalence record: `RELEASE_EQUIVALENCE.md`. Upstream repository: https://github.com/mahmood726-cyber/allmeta. PR #143 head: `0bea27b258fe73a1f7a1dbd90693c5ce7a8eb4b9` (merge `acdb28371560a797eb256c591edb5969d4675f62`); PR #160 head: `dd9f2a863dffc0f34f715442f1698633cfb133a2` (historical plus capture `5373102e219ea1154b845496a68d2150703b91af`).

Historical evidence is preserved: `app/original` is commit `7966530de875d22253f0557c7b447ed9d917685d`; `app/historical-patched` is that commit plus `bench/fix.patch`. The original source manifest, bundle manifest, EOL record, compressed captures, R references and expected counts remain unchanged. On the v1.8.0 bytes, the Node primary capture scored against the archived netmeta reference gives 76601/76601, the focused capture 319/319, and the plus replay `PLUS NODE REPLAY 643413/643413` (see `RELEASE_EQUIVALENCE.md`; the fresh R refit of `validate.R` was not re-run for this release fill). The plus browser tier was re-run on the v1.8.0 bytes in Edge 155: 42/42 passed (`plus/evidence/browser-v180/`). It records the v1.8.0 behaviour that invalid input clears results (allmeta 1f5ce9e, the pull request #160 review fix); the earlier run that kept results is kept as history in `plus/evidence/browser/`.

## What is validated

The page fits a two-arm contrast network (A, B, effect, SE; optional study ID) under fixed effect (FE), generalized DerSimonian-Laird (DL) or generalized Paule-Mandel (PM), with one consistency-model tau-squared. It reports node-splitting (back-calculation: direct minus indirect at the full-network tau-squared, SE sqrt(SEdirect^2 + SEindirect^2), two-sided normal p) and a design-by-treatment global Q. The reference is **R 4.6.0, netmeta 3.7.0** (`netmeta`, `netsplit(method = "Back-calculation")`, `decomp.design`), with meta 8.5.0, metadat 1.6.0, metafor 5.2.1 and jsonlite 2.0.0. FE is compared with the `Between designs` row of `decomp.design`; DL/PM use `Q.inc.random.preset` with `tau.preset` equal to the consistency-model tau. netmeta has no PM estimator, so the PM tau-squared oracle solves Q(tau-squared) = k - p with metafor's internal `.QE.func` on the uncentered network design (`bench/diagnose_pm.R` documents why a centered `rma` fit is not the oracle) and passes it to netmeta as `tau.preset`. No R package code was patched.

Corpus: 127 installed datasets enumerated (13 netmeta, 114 metadat); 36 supply **540 configurations** (180 each FE/DL/PM; 336 full-input and 204 explicitly labelled two-arm-only subsets), 2 to 136 contrasts, no truncation. Reference statuses: 291 fitted, 249 refused by an explicit input-support gate (204 multi-arm studies, 33 disconnected networks, 12 with fewer than three contrasts). **Refusal checks establish refusal behaviour only; multi-arm numerical inference is not validated.**

Historical comparison (Node execution of the shipped page script and the shipped export serializer; see Limits): original **79869/83592 checks pass**, patched **76601/76601 checks pass**. Focused checks, counted separately: original 194/319, patched 319/319. The denominators differ because the original page emitted invalid or extra splits and their plot/text elements; configuration and reference keys are identical. Tolerances: relative abs(app - ref)/max(1, abs(ref)) at most 1e-9 for FE/DL and 1e-6 for PM-derived quantities; p-values 1e-9 absolute; counts, memberships, refusal strings and displayed strings exact.

## Reproduce

Requirements: R 4.6.0 with exactly netmeta 3.7.0, meta 8.5.0, metadat 1.6.0, metafor 5.2.1 and jsonlite 2.0.0; Python 3 (standard library only); Node.js (24.13.0 used for the capture harness). No package is installed and no network access is needed. Set `R_LIBS_USER` / `R_LIBS` to the libraries holding those versions and `R_ENVIRON_USER` to an empty file (`NUL` on Windows). From the archive root:

```text
Rscript validate.R
python analysis/verify_archive.py
python analysis/test_safeguards.py
```

`validate.R` prints `.libPaths()` and every package version and refuses to run on any version difference; SHA-256 checks the complete inventory in `SOURCE_SHA256.json`; then, in one R process, **refits all 540 configurations from `data/corpus.json`** with no archived fit reused, plus the focused R oracles. It requires the fresh fits to match the archived reference (`results/reference/`) within 1e-12 (two documented allowances: the bundle reused cached FE/DL and refused records written before its script tagged every record with `pm_reference`, so that tag may be absent from the archived record only; and netmeta orders `netsplit` rows by locale collation of treatment labels, so split rows are matched by their comparison name, not position, exactly as the comparison code does). The illustrative multi-arm diagnostic is held to 1e-9. It then stages the unchanged `bench/run_app.cjs` and `bench/test_focused.cjs` harnesses under `.validate-work/capture`, runs `node run_app.cjs patched` and `node test_focused.cjs patched` against the current candidate and fresh focused R oracles, and compares those new candidate outputs and the archived original outputs with the **fresh** fits using the bundle's comparison code (`analysis/compare_archive.py`, which differs from `bench/compare.py` only in file paths; see `analysis/compare_archive.diff`), requires every per-quantity count to equal `expected/paper_values.json`, and exits nonzero on any failure. An existing `.validate-work/` is refused so a stale result cannot pass; move it aside before a new run. The final lines are:

```text
Focused patched (fresh candidate Node observations; 268 rescored against fresh R): 319/319 focused checks pass
Runtime: ... seconds
76601/76601 checks pass
```

The refit is a long single-process computation (the bundle's per-configuration fit times sum to about 2,600 seconds). `verify_archive.py` checks the inventory, that every historical carried-over file is byte-identical to the validation bundle's own manifest (`bench/bundle-archive-manifest.json`), the xz compression proofs, that `app/original` matches the upstream hashes in `app/source-manifest.json`, that `app/original` and `app/historical-patched` reconstruct `bench/fix.patch` exactly (using the same unified-diff generator, without Git writes), and that the current `app/patched` matches the separate candidate pins, keyed coverage, text hygiene and metadata. `test_safeguards.py` plants a defect for each gate and requires it to be rejected.

## Plus layer: the leave-one-study-out panel (allmeta pull request #160)

`plus/` validates the added panel at the head of `feat/nma-inconsistency-plus` (commit 5373102e219ea1154b845496a68d2150703b91af; `plus/app/SOURCE.json`). `validate.R` ends by sourcing `plus/validate-plus.R`: version check, SHA-256 checks of the panel's files and pinned references, a fresh native-R refit of a seeded subset of the 153 configurations (every study removed in turn; `PLUS_FULL=1` refits all 153, `PLUS_PLANT=1` plants a defect and must fail), and the Node.js replay `PLUS NODE REPLAY 643413/643413`. Recorded evidence and its limits: `plus/README.md`.

## Faults found and fixed

| Fault (original page) | Configuration / quantity | Original | netmeta reference | Patched |
|---|---|---:|---:|---:|
| Polynomial normal-tail approximation; p error above 1e-9 | `netmeta::Baker2009::exac::OR::two-arm-only::FE`, split p, Fluticasone+Salmeterol vs Placebo | 0.21390383531984902 | 0.2139036987533419 | 0.21390369875334259 |
| No-loop network reported residual Q as an inconsistency test | `netmeta::Franchini2012::change::MD::two-arm-only::FE`, global Q / df | 1.6088517069221426 / 2 | 0 / 0 (not testable) | 0 / 0 (not testable) |
| Multi-arm studies flattened into independent rows (false precision) | `netmeta::Senn2013::stored::MD::full::FE`, global Q / df / p | 22.4517017018 / 6 / 0.00100253367769 | 22.5302712697 / 7 / 0.00205701423801 | refused: unsupported covariance |
| Multi-arm studies flattened | `netmeta::smokingcessation::cessation::OR::full::FE` | 3.58786646349 / 3 / 0.309543664802 | 15.2203370209 / 7 / 0.0332764724516 | refused |
| Multi-arm studies flattened | `netmeta::Baker2009::exac::OR::full::FE` | 5.85422513126 / 9 / 0.754414794726 | 17.0607068438 / 12 / 0.147327956426 | refused |

Further faults, all fixed by the patch: indirect evidence detected by matrix-inversion failure, so roundoff in a singular reduced network produced huge or nonfinite indirect SEs (now explicit graph reachability); stale results retained after invalid input and no refusal reason (now cleared, with a reason); undefined p exported as NaN in CSV/Markdown but null in JSON (now consistently null/blank); quoted commas, pipe characters, HTML and object-prototype names mishandled in labels and pair keys; forest-plot domain computed from point estimates only, clipping confidence limits. Per-quantity before/after counts are in `results/comparison-original.txt`, `results/comparison-patched.txt` and `expected/paper_values.json`; the multi-arm rows above come from `results/multiarm-diagnostic.json` (native-study versus flattened netmeta fits) and are diagnostics, not coverage claims.

## Limits

- App outputs were captured by executing the shipped inline page script and shared `results-export.js` in a Node VM with a minimal DOM adapter (Edge launch failed with spawn EPERM). This verifies engine results, generated table/SVG markup, exact strings and the actual export blobs. It does **not** verify real browser layout, accessibility, download UI, PNG/PDF/JPG rendering, autosave or navigation. `validate.R` now re-runs the candidate primary and focused Node captures as well as R; original-page observations remain archived. The primary snapshot is an engine/serializer/bus capture subset, not a complete browser deployment (plus scripts and live-validation assets are carried separately under `plus/app`).
- Historical focused checks remain archived. The candidate rerun captures all 319 checks anew; the 268 with R oracles (normal p-values, bus transformations) use the fresh R values, and the remaining 51 are also re-executed in Node. Original-page focused checks retain their historical observations.
- Scope is independent two-arm studies: the page has no study-covariance model, so multi-arm and repeated-study inputs are refused, never numerically validated. Two-arm-only subsets remove whole multi-arm studies and are separate configurations. Package examples include dependent or hypothetical rows; they are software fixtures, not clinical evidence.
- The PM reference uses a reference-side root-finding oracle because netmeta lacks PM; agreement for PM-derived quantities is at 1e-6.
- Only R 4.6.0 with the listed package versions was used; other versions are refused rather than assumed equivalent.

| Item | Static | Dynamic / source-backed |
|---|---|---|
| Rules | FE/DL/PM, tolerances, page semantics | Fresh netmeta refit of every configuration |
| Corpus | Archived corpus, recipes, ledgers | Keyed coverage, refusal reasons, split ledger |
| Findings | Expected per-quantity counts | Recomputed comparison against fresh fits |
| Provenance | Source commit, fix.patch, bundle tar SHA-256 | Inventory, historical bundle-manifest identity, exact patch reconstruction, candidate pins |

## Layout

`app/` holds the original, historical-patched and current candidate patched page snapshots with their shared assets, `app-sha256.json` and the upstream `source-manifest.json`. `data/` holds the corpus, dataset/configuration/refusal/split ledgers, construction attempts and `bundle-provenance.json` (source tar SHA-256 and run record). `results/` holds the archived app captures (`app-*.json.xz`, deterministic xz; `analysis/compression_proof.json` records raw and stored hashes), the 540 archived R reference records, comparison outputs and focused results. `expected/paper_values.json` pins the counts. `bench/` keeps the validation bundle's own scripts, logs, results narrative (`RESULTS.md`), `fix.patch` and installed package documentation (GPL-licensed upstream text). `analysis/` holds the fresh-refit, comparison, verifier and safeguard code. Machine-specific library paths in bundle logs were already replaced by portable placeholders in the bundle. MIT applies to the archive tooling.

## Re-cut maintenance

`python analysis/refresh_inventory.py` regenerates only `app/app-sha256.json` and `SOURCE_SHA256.json`, using `analysis/common.py` hashing and file-selection rules. This entry point was added because the archive shipped readers but no standalone writer for these two inventories. Never regenerate the historical bundle manifest, upstream source manifest, EOL or compression proofs to conceal a changed historical file. `python analysis/verify_archive.py` and `python analysis/test_safeguards.py` are fast checks. The release identifiers are filled (v1.8.0, DOI 10.5281/zenodo.23515177); the verifier rejects any remaining release placeholder.

The primary and focused counts from the fresh R refit are produced by the long `Rscript validate.R` run. The existing expected values are gates, not automatically rewritten results: changed counts cause failure and require review. The default run also includes the existing sampled plus R refit and full plus Node replay; no included plus source mismatch requires a seven-hour `PLUS_FULL=1` run. The recorded default full-archive runtime is 3 h 9 min, with about 2,600 seconds summed primary fit time; allow several hours on this machine.
