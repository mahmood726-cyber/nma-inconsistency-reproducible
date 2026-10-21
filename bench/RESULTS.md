# NMA inconsistency validation

Source commit: `7966530de875d22253f0557c7b447ed9d917685d`. Source files were copied without editing the checkout. Proposed app-only changes are in [fix.patch](fix.patch). No commit or push was made.

Original: **79869/83592 checks pass**. Patched: **76601/76601 checks pass**. Focused checks, counted separately: **194/319** original and **319/319** patched.

These totals include numerical, coverage, export, generated-markup and input-support checks. **Multi-arm refusals are not numerical parity passes. Browser rendering was not validated.** The different original/patched denominators reflect invalid/extra original splits and their emitted plot/text elements; the configuration and reference keys are identical.

## Coverage

127 installed datasets were enumerated programmatically (13 netmeta and 114 metadat). 36 datasets supplied 540 configurations: 180 each for FE, DL and PM; 336 full-input and 204 explicitly labeled two-arm-only subset configurations. Inputs range from 2 to 136 contrasts. No upper cap or numerical truncation was imposed.

All documented network datasets in the installed netmeta/metadat documentation are included, together with additional explicit-treatment star networks. Package aliases remain separate candidates. [dataset-ledger.csv](dataset-ledger.csv) records every inclusion/exclusion and links its installed documentation; [construction-attempts.json](construction-attempts.json) records every recipe and warning, with no unresolved construction errors. [configuration-ledger.csv](configuration-ledger.csv) supplies unique keys, source recipes, input hashes and statuses. [row-exclusions.json](row-exclusions.json) records invalid pairwise inputs, package omissions and 16 Lopez studies with repeated identical treatment-arm labels whose standardized change scores were not aggregated under an invented assumption.

The corpus uses stored effects where provided; otherwise meta::pairwise or metafor::escalc constructs contrasts from documented arm outcomes. Binary arms use OR and RR, continuous raw arms MD and SMD, dietary-fat rates IRR, and the Lopez documented arm-change contrasts use diff1-diff2 and sqrt(se1²+se2²). Zero cells receive 0.5 only when required; all-zero binary studies are retained when the selected construction allows finite estimates. Distinct endpoints are separate recipes. Both engines consume the same serialized effects and SEs; SE-squared is the variance. Seventeen significant digits preserve binary64 inputs. Study identifiers are retained; multi-arm or repeated-study rows are never relabeled as independent trials.

Reference/support statuses: `{'refused': 249, 'ok': 291}`. Reasons: `{'Multi-arm studies are unsupported: correlated contrasts require study covariance.': 204, 'The treatment network is disconnected.': 33, 'At least 3 valid contrasts are required.': 12}`. All refusals and original/patched responses are in [refusal-ledger.csv](refusal-ledger.csv). The R reference applies an explicit input-support gate before numerical fitting; matching that gate establishes refusal behavior only. Full native multi-arm numerical validation is outside this engine’s supported scope. Two-arm subsets remove whole identified multi-arm studies and are separate configurations, not replacements for the full input.

## Page contract and reference

The shipped page accepts A, B, effect and SE contrasts, treats every row as independent, and offers FE, generalized DL and generalized PM. It estimates a single τ² from consistency-model residuals; this is not a within-design heterogeneity estimate. The default is FE. It uses a normal 95% quantile of 1.959963984540054. There is no treatment/reference selector, confidence-level selector, other τ² estimator, Knapp–Hartung option, or study-count cap. Fewer than three accepted contrasts originally return silently; malformed numeric rows are silently filtered. The patch clears and reports refusals, accepts an optional study-ID column, and refuses multi-arm/repeated-study data and disconnected networks.

Node splitting removes all direct rows for a pair, fits the remaining network at the full-network τ², pools the direct rows at that same τ², and forms direct minus indirect with SE sqrt(SEdirect²+SEindirect²), z and two-sided normal p. For independent two-arm studies this matches netmeta back-calculation, and the fixed-τ split underlying SIDE/SIDDE. It is not a multi-arm SIDDE implementation. All signed quantities use lexically sorted A vs B; R’s reversed comparison names are explicitly sign-converted, never compared by absolute effect. Exact graph reachability determines which pairs have an independent indirect path. [split-ledger.csv](split-ledger.csv) records every tested or untestable pair.

The global statistic compares consistency and per-pair design models using the same weights. FE is compared to the Between designs row of netmeta::decomp.design; DL/PM use Q.inc.random.preset with tau.preset equal to the consistency-model τ. This differs from decomp.design’s default random test, which estimates τ within designs. A network without loops has Q=0, df=0 and undefined p; it cannot be labeled evidence of consistency.

R was 4.6.0; netmeta 3.7.0, meta 8.5.0, metadat 1.6.0, metafor 5.2.1 and jsonlite 2.0.0. Every R log prints .libPaths() and these versions. Portable library placeholders replace machine paths in logs. Startup locale warnings were captured. Installed help and source snapshots are in documentation/.

netmeta supports DL/ML/REML, not PM. The PM oracle therefore calls the installed metafor .QE.func with the **uncentered** outcome vector and the network contrast design, then stats::uniroot for Q(τ²)=k-p, and passes sqrt(τ²) into netmeta. Its bracket doubles from max(1,var(effect)); tolerance is .Machine$double.eps^0.75, maxiter=1000. The installed rma.uni centers outcomes internally even for this no-intercept design, so direct rma(...,method="PM",intercept=FALSE) was diagnosed and rejected as the oracle. [diagnose_pm.log](diagnose_pm.log) and documentation/PM-QE-source.txt document this reference-side correction. No R-package code was patched.

The original PM app solver uses 60 bisections and an absolute 1e-10 interval cutoff; the patch uses 100 and 1e-13*max(1,mid). Estimates, SEs, Q and τ² use relative abs(app-ref)/max(1,abs(ref)) ≤1e-9 for FE/DL and ≤1e-6 for PM-derived quantities. P-values always use 1e-9 absolute. Counts, treatment/pair membership, refusals and strings at their displayed precision are exact. No relaxed post-hoc tolerance or omitted failure is counted as a pass.

## Execution and evidence limits

The permitted Node route was used (Node v24.13.0). Edge launch through the available Playwright driver failed with spawn EPERM; npm installation found no offline cached @playwright/test. The runner executes the page’s shipped inline JavaScript and original shared results-export.js in a VM with a minimal DOM adapter. Statistical functions and rendering functions are unmodified in the original run. There is no independent JavaScript reimplementation of the estimator. The adapter captures generated table/plot markup and actual Blob download contents for JSON, CSV, data Markdown, and both Methods+Results reports.

This verifies engine results, generated markup, exact strings, serializer consistency, and SVG coordinates. It does **not** verify real DOM parsing/layout, accessibility behavior, browser download UI, chart rasterization, PNG/PDF/JPG files, autosave, navigation/continue-bar interactions, or screenshot fidelity. Markup checks must not be described as live Edge UI evidence. Exported p=NaN versus JSON null was tested explicitly. Metadata timestamps are dynamic; reported statistics are checked independently of them.

## Faults and changes

1. **Normal-tail approximation:** index.html:161 used a polynomial CDF whose errors exceed the required 1e-9 p tolerance. The patch uses the existing accurate chi-square CDF at z² with one degree of freedom.
2. **Nonexistent indirect evidence:** index.html:273 relied on inversion failure to detect disconnected reduced networks. Roundoff can leave a nonzero pivot in a singular Laplacian, yielding huge or nonfinite indirect SEs. The patch explicitly checks graph reachability.
3. **No-loop global test:** index.html:311 returned residual heterogeneity Q and df as the inconsistency test. The patch returns 0/0/undefined and labels the test unavailable. Global Q is also calculated from nested fitted-value differences to avoid subtraction cancellation.
4. **Lost study dependence:** index.html:553 discarded study IDs and full-arm designs during bus conversion. The patch refuses multi-arm bus inputs, preserves optional study IDs for independent two-arm rows, and states the supported scope in the page and README. This prevents false precision; it does not add multi-arm inference.
5. **Stale results and export undefined values:** index.html:391 retained previous results after invalid input. The patch clears all result state and supplies a reason, including empty/unsupported bus imports. At index.html:446, undefined p was NaN in CSV/Markdown but null in JSON; it is now consistently null/blank on export.
6. **Labels and keys:** index.html:126, 260, and 421 mishandled quoted commas, pipe-delimited pair keys, HTML labels and object-prototype names. The patch parses quoted fields, escapes rendered labels, uses unambiguous pair keys and prototype-free estimate objects.
7. **Clipped CIs:** index.html:464 based the plot domain on point estimates alone. The patch includes all direct and indirect confidence limits.

Before/after examples from saved runs:

| Check | Configuration / quantity | Original | Reference / required | Patched |
|---|---|---:|---:|---:|
| split_p | `netmeta::Baker2009::exac::OR::two-arm-only::FE::Fluticasone+Salmeterol vs Placebo` | 0.21390383531984902 | 0.2139036987533419 | 0.21390369875334259 |
| dbt_Q | `netmeta::Franchini2012::change::MD::two-arm-only::FE` | 1.6088517069221426 | 0 | 0 |
| dbt_df | `netmeta::Franchini2012::change::MD::two-arm-only::FE` | 2 | 0 | 0 |
| Multi-arm global Q/df/p | `netmeta::Senn2013::stored::MD::full::FE` | 22.4517017018 / 6 / 0.00100253367769 | 22.5302712697 / 7 / 0.00205701423801 | refused: unsupported covariance |
| Multi-arm global Q/df/p | `netmeta::smokingcessation::cessation::OR::full::FE` | 3.58786646349 / 3 / 0.309543664802 | 15.2203370209 / 7 / 0.0332764724516 | refused: unsupported covariance |
| Multi-arm global Q/df/p | `netmeta::Baker2009::exac::OR::full::FE` | 5.85422513126 / 9 / 0.754414794726 | 17.0607068438 / 12 / 0.147327956426 | refused: unsupported covariance |

The three multi-arm rows above are actual native-study-versus-flattened netmeta diagnostic runs, not coverage claims for all multi-arm networks. Focused checks also validate shared-bus OR/RR/MD/SMD transformations, zero-cell corrections and small-sample SMD against metafor::escalc; normal p-values against R pnorm; quoted/HTML/pipe/prototype labels; bridge membership; stale-input handling; and empty/unsupported/multi-arm bus refusal.

## Counts by check type

| Type | Original pass/checks | Patched pass/checks |
|---|---:|---:|
| contract | 3866/4260 | 4260/4260 |
| coverage | 1625/1625 | 1625/1625 |
| display | 2501/2648 | 2265/2265 |
| export | 21375/21669 | 21717/21717 |
| numerical | 16523/17928 | 17928/17928 |
| plot | 33674/34175 | 27519/27519 |
| refusal | 305/1287 | 1287/1287 |

## Per-quantity results

| Quantity | Original pass/checks | Patched pass/checks | Original max difference | Patched max difference |
|---|---:|---:|---:|---:|
| Q | 291/291 | 291/291 | 5.66259172732e-16 | 5.66259172732e-16 |
| Qrandom | 291/291 | 291/291 | 7.02689314144e-10 | 3.46389583684e-12 |
| app_coverage | 1/1 | 1/1 | 0 | 0 |
| app_evidence | 540/540 | 540/540 | 0 | 0 |
| app_unique | 1/1 | 1/1 | 0 | 0 |
| corpus_unique | 1/1 | 1/1 | 0 | 0 |
| csv_array | 582/582 | 582/582 | 0 | 0 |
| csv_keys | 291/291 | 291/291 | 0 | 0 |
| csv_number | 8526/8526 | 8550/8550 | 0 | 0 |
| csv_scalar | 291/438 | 438/438 | 1 | 0 |
| dbt_Q | 144/291 | 291/291 | 197.940871541 | 1.02380705505e-12 |
| dbt_df | 144/291 | 291/291 | 1 | 0 |
| dbt_p | 144/144 | 144/144 | 4.96865770749e-10 | 6.10955730451e-13 |
| dbt_p_undefined | 147/147 | 147/147 | 0 | 0 |
| df | 291/291 | 291/291 | 0 | 0 |
| direct_k | 1245/1245 | 1245/1245 | 0 | 0 |
| direct_mean | 1245/1245 | 1245/1245 | 4.04868361059e-11 | 7.46902539817e-14 |
| direct_se | 1245/1245 | 1245/1245 | 9.27928567318e-11 | 1.77746706242e-13 |
| display_global | 291/291 | 291/291 | 0 | 0 |
| display_model_tau | 291/291 | 291/291 | 0 | 0 |
| display_split | 1628/1628 | 1245/1245 | 0 | 0 |
| estimatesRandom_est | 1659/1665 | 1665/1665 | 1.07895747892e-10 (6 invalid) | 1.44695366799e-12 |
| estimatesRandom_se | 1659/1665 | 1665/1665 | 1.217282386e-10 (6 invalid) | 9.37583344296e-13 |
| estimates_est | 1659/1665 | 1665/1665 | 1.44695366799e-12 (6 invalid) | 1.44695366799e-12 |
| estimates_se | 1659/1665 | 1665/1665 | 1.21846976953e-14 (6 invalid) | 1.21846976953e-14 |
| execution_error | 521/540 | 540/540 | 1 | 0 |
| indirect_mean | 1245/1245 | 1245/1245 | 1.03970054788e-10 | 7.00473012927e-12 |
| indirect_se | 1245/1245 | 1245/1245 | 7.77941044916e-11 | 2.25992289327e-13 |
| input_k | 285/291 | 291/291 | 1 | 0 |
| input_status | 291/540 | 540/540 | 1 | 0 |
| json_export | 540/540 | 540/540 | 0 | 0 |
| markdown_array | 582/582 | 582/582 | 0 | 0 |
| markdown_keys | 291/291 | 291/291 | 0 | 0 |
| markdown_number | 8526/8526 | 8550/8550 | 0 | 0 |
| markdown_scalar | 291/438 | 438/438 | 1 | 0 |
| model | 291/291 | 291/291 | 0 | 0 |
| parsed_rows | 285/291 | 291/291 | 1 | 0 |
| plot_CI_coordinate | 6332/6332 | 4980/4980 | 0 | 0 |
| plot_CI_in_view | 5844/6332 | 4980/4980 | 1 | 0 |
| plot_CI_y | 6332/6332 | 4980/4980 | 0 | 0 |
| plot_finite_evidence | 278/291 | 291/291 | 1 | 0 |
| plot_labels | 278/278 | 291/291 | 0 | 0 |
| plot_line_count | 278/278 | 291/291 | 0 | 0 |
| plot_marker | 12664/12664 | 9960/9960 | 0 | 0 |
| plot_marker_count | 278/278 | 291/291 | 0 | 0 |
| plot_viewbox | 278/278 | 291/291 | 0 | 0 |
| plot_zero_line | 1112/1112 | 1164/1164 | 0 | 0 |
| reference_coverage | 1/1 | 1/1 | 0 | 0 |
| reference_evidence | 540/540 | 540/540 | 0 | 0 |
| reference_unique | 1/1 | 1/1 | 0 | 0 |
| reference_valid | 540/540 | 540/540 | 0 | 0 |
| refusal_plot_clear | 0/249 | 249/249 | 1 | 0 |
| refusal_reason | 0/249 | 249/249 | 1 | 0 |
| refusal_table_clear | 14/249 | 249/249 | 1 | 0 |
| report_markdown_data | 291/291 | 291/291 | 0 | 0 |
| report_text_data | 291/291 | 291/291 | 0 | 0 |
| split_diff | 1245/1245 | 1245/1245 | 1.03972053189e-10 | 7.00473012927e-12 |
| split_membership | 81/291 | 291/291 | 1 | 0 |
| split_p | 11/1245 | 1245/1245 | 1.39267357979e-07 | 1.04311004279e-12 |
| split_seDiff | 1245/1245 | 1245/1245 | 9.22040221951e-11 | 2.2292586053e-13 |
| split_unique | 291/291 | 291/291 | 0 | 0 |
| split_z | 1245/1245 | 1245/1245 | 7.46007478014e-10 | 1.91257022894e-11 |
| table_row_count | 291/291 | 291/291 | 0 | 0 |
| tau2 | 291/291 | 291/291 | 4.58284937777e-11 | 4.56953919148e-13 |
| text_export_present | 873/873 | 873/873 | 0 | 0 |
| treatment_membership | 285/291 | 291/291 | 1 | 0 |
| untestable_label | 0/147 | 147/147 | 1 | 0 |

Exact-check maxima are 0/1 mismatch indicators. Numerical maxima use the specified relative scale, except p-values (absolute). CSV/Markdown numbers are compared exactly to JSON. Plot coordinates use 1e-9 relative; bounds use exact inclusion in the viewBox.

## Reproduction

On the supplied Windows image, the wrapper locates the requested R installation and libraries relative to the user home/audit tree. For another installation set RSCRIPT, AUDIT_R_LIBS_USER and AUDIT_R_LIBS; set ALLMETA_ROOT for a different source checkout. No installation or network connection is needed. Commands run from the audit directory:

```text
python setup.py
python run_r.py inventory.R
python run_r.py corpus.R
python review_inventory.py
python make_patch.py
node run_app.cjs original
node run_app.cjs patched
python run_r.py reference.R 1 3
python run_r.py reference.R 2 3
python run_r.py reference.R 3 3
python run_r.py diagnose_pm.R
python run_r.py focused.R
python run_r.py bus_reference.R
node test_focused.cjs original
node test_focused.cjs patched
python compare.py original
python compare.py patched
python report.py
python verify_archive.py
```

The three reference commands ran concurrently. They preserve completed keyed results on restart; PM records are reused only when marked with the final uncentered-package-QE oracle. For a clean rerun use a new audit directory and regenerate the inputs. The diagnosis deliberately shows why the earlier centered PM construction is unsuitable. Intermediate partial comparison totals are overwritten; the final logs below are authoritative.

Verbatim final comparison lines:

```text
79869/83592 checks pass
76601/76601 checks pass
194/319 focused checks pass (original; Node, not browser)
319/319 focused checks pass (patched; Node, not browser)
```

## Dataset decisions

| Package | Dataset | Configurations | Decision/reason |
|---|---|---:|---|
| netmeta | Baker2009 | 12 | included: explicit treatment identities and contrast/arm outcome data; full network plus two-arm subset where needed |
| netmeta | Dogliotti2014 | 12 | included: explicit treatment identities and contrast/arm outcome data; full network plus two-arm subset where needed |
| netmeta | Dong2013 | 12 | included: explicit treatment identities and contrast/arm outcome data; full network plus two-arm subset where needed |
| netmeta | Franchini2012 | 12 | included: explicit treatment identities and contrast/arm outcome data; full network plus two-arm subset where needed |
| netmeta | Gurusamy2011 | 12 | included: explicit treatment identities and contrast/arm outcome data; full network plus two-arm subset where needed |
| netmeta | Linde2015 | 60 | included: explicit treatment identities and contrast/arm outcome data; full network plus two-arm subset where needed |
| netmeta | Linde2016 | 6 | included: explicit treatment identities and contrast/arm outcome data; full network plus two-arm subset where needed |
| netmeta | Senn2013 | 6 | included: explicit treatment identities and contrast/arm outcome data; full network plus two-arm subset where needed |
| netmeta | Stowe2010 | 12 | included: explicit treatment identities and contrast/arm outcome data; full network plus two-arm subset where needed |
| netmeta | Woods2010 | 12 | included: explicit treatment identities and contrast/arm outcome data; full network plus two-arm subset where needed |
| netmeta | dietaryfat | 6 | included: explicit treatment identities and contrast/arm outcome data; full network plus two-arm subset where needed |
| netmeta | parkinson | 12 | included: explicit treatment identities and contrast/arm outcome data; full network plus two-arm subset where needed |
| netmeta | smokingcessation | 12 | included: explicit treatment identities and contrast/arm outcome data; full network plus two-arm subset where needed |
| metadat | dat.aloe2013 | 0 | excluded: Studies on the Association Between Supervision Quality and Various Outcomes in Social, Mental Health, and Child Welfare Workers; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.anand1999 | 0 | excluded: Studies on the Effectiveness of Oral Anticoagulants in Patients with Coronary Artery Disease; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.anker2025 | 0 | excluded: Cardiology Example Data with Subgroup and Interaction Effects; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.assink2016 | 0 | excluded: Studies on the Association between Recidivism and Mental Health; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.axfors2021 | 12 | included: explicit treatment identities and contrast/arm outcome data; full network plus two-arm subset where needed |
| metadat | dat.bakdash2021 | 0 | excluded: Dataset on Situation Awareness and Task Performance Associations; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.baker2009 | 12 | included: explicit treatment identities and contrast/arm outcome data; full network plus two-arm subset where needed |
| metadat | dat.bangertdrowns2004 | 0 | excluded: Studies on the Effectiveness of Writing-to-Learn Interventions; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.bartos2023 | 0 | excluded: Results of 350,757 Coin Flips to Examine Same-Side Bias; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.baskerville2012 | 0 | excluded: Studies on the Effectiveness of Practice Facilitation Interventions; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.bassler2004 | 0 | excluded: Studies on Ketotifen Alone or as Additional Medication for Long-Term Control of Asthma and Wheeze in Children; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.bauer2002 | 0 | excluded: one treatment contrast (OM-89 versus control); no third treatment identity |
| metadat | dat.bcg | 0 | excluded: Studies on the Effectiveness of the BCG Vaccine Against Tuberculosis; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.begg1989 | 0 | excluded: two treatment types (bone-marrow transplantation and chemotherapy); arm-level example, not a multi-treatment network |
| metadat | dat.berkey1998 | 0 | excluded: Studies on Treatments for Periodontal Disease; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.berkey1998r | 0 | excluded: Studies on Treatments for Periodontal Disease; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.besson2016 | 0 | excluded: heterogeneous animal manipulations, outcomes, repeated animals and shared controls; no documented treatment-node network or unique independent trial reconstruction; not relabeled as an NMA |
| metadat | dat.bonett2010 | 0 | excluded: Studies on the Reliability of the CES-D Scale; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.bornmann2007 | 0 | excluded: Studies on Gender Differences in Grant and Fellowship Awards; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.bourassa1996 | 0 | excluded: Studies on the Association between Handedness and Eye-Dominance; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.cannon2006 | 0 | excluded: Studies on the Effectiveness of Intensive Versus Moderate Statin Therapy for Preventing Coronary Death or Myocardial Infarction; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.chiarito2020 | 24 | included: explicit treatment identities and contrast/arm outcome data; full network plus two-arm subset where needed |
| metadat | dat.cohen1981 | 0 | excluded: correlations; control is a study-design moderator, not a comparator-treatment identity |
| metadat | dat.colditz1994 | 0 | excluded: Studies on the Effectiveness of the BCG Vaccine Against Tuberculosis; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.collins1985a | 18 | included: explicit treatment identities and contrast/arm outcome data; full network plus two-arm subset where needed |
| metadat | dat.collins1985b | 0 | excluded: Studies on the Effects of Diuretics in Pregnancy; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.craft2003 | 0 | excluded: Studies on the Relationship between the Competitive State Anxiety Inventory-2 and Sport Performance; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.crede2010 | 0 | excluded: Studies on the Relationship between Class Attendance and Grades in College Students; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.crisafulli2020 | 0 | excluded: Duchenne Muscular Dystrophy (DMD) Prevalence Data; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.curtin2002 | 0 | excluded: Studies on Potassium Supplementation to Reduce Diastolic Blood Pressure; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.curtis1998 | 0 | excluded: elevated versus ambient CO2; xtrt/level are experimental moderators, not a documented multi-treatment trial network |
| metadat | dat.dagostino1998 | 48 | included: explicit treatment identities and contrast/arm outcome data; full network plus two-arm subset where needed |
| metadat | dat.damico2009 | 0 | excluded: Studies on Topical plus Systemic Antibiotics to Prevent Respiratory Tract Infections; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.debruin2009 | 0 | excluded: Studies on Standard Care Quality and HAART-Adherence; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.demir2022 | 0 | excluded: Studies on the Reliability of the MIBS Scale; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.dogliotti2014 | 12 | included: explicit treatment identities and contrast/arm outcome data; full network plus two-arm subset where needed |
| metadat | dat.dong2013 | 12 | included: explicit treatment identities and contrast/arm outcome data; full network plus two-arm subset where needed |
| metadat | dat.dorn2007 | 0 | excluded: Studies on Complementary and Alternative Medicine for Irritable Bowel Syndrome; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.dumouchel1994 | 0 | excluded: Nitrogen dioxide data set; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.egger2001 | 0 | excluded: Studies on the Effectiveness of Intravenous Magnesium in Acute Myocardial Infarction; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.feng2019 | 0 | excluded: Studies on the Prevalence of Depression After Myocardial Infarction; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.fine1993 | 0 | excluded: Studies on Radiation Therapy with or without Adjuvant Chemotherapy in Patients with Malignant Gliomas; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.franchini2012 | 12 | included: explicit treatment identities and contrast/arm outcome data; full network plus two-arm subset where needed |
| metadat | dat.frank2008 | 0 | excluded: Studies on the Association Between the CASP8 -652 6N del Promoter Polymorphism and Breast Cancer Risk; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.furukawa2003 | 0 | excluded: Studies on Low Dosage Tricyclic Antidepressants for the Treatment of Depression; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.gibson2002 | 0 | excluded: Studies on the Effectiveness of Self-Management Education and Regular Medical Review for Adults with Asthma; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.graves2010 | 0 | excluded: Studies on the Effectiveness of Injected Cholera Vaccines; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.greb2008 | 0 | excluded: Trials on High-Dose Chemotherapy with Autologous Stem Cell Transplantation in Aggressive Non-Hodgkin Lymphoma; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.greenland1992 | 0 | excluded: Case-Control Studies on the Impact of Alcohol Consumption on Breast Cancer Risk; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.gurusamy2011 | 12 | included: explicit treatment identities and contrast/arm outcome data; full network plus two-arm subset where needed |
| metadat | dat.hackshaw1998 | 0 | excluded: Studies on the Risk of Lung Cancer in Women Exposed to Environmental Tobacco Smoke; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.hahn2001 | 0 | excluded: Studies on the Effectiveness of Different Rehydration Solutions for the Prevention of Unscheduled Intravenous Infusion in Children with Diarrhoea; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.hannum2020 | 0 | excluded: Studies Comparing Objective and Subjective Olfactory Loss in COVID-19 Patients; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.hart1999 | 6 | included: explicit treatment identities and contrast/arm outcome data; full network plus two-arm subset where needed |
| metadat | dat.hartmannboyce2018 | 12 | included: explicit treatment identities and contrast/arm outcome data; full network plus two-arm subset where needed |
| metadat | dat.hasselblad1998 | 12 | included: explicit treatment identities and contrast/arm outcome data; full network plus two-arm subset where needed |
| metadat | dat.higgins2008 | 0 | excluded: Trials on Haloperidol in Schizophrenia; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.hine1989 | 0 | excluded: Studies on Prophylactic Use of Lidocaine After a Heart Attack; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.huber2000 | 0 | excluded: individual-patient data for Uro-Vaxom versus placebo only; two treatments |
| metadat | dat.ishak2007 | 0 | excluded: Studies on Deep-Brain Stimulation in Patients with Parkinson's disease; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.kalaian1996 | 0 | excluded: Studies on the Effectiveness of Coaching for the SAT; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.karner2014 | 0 | excluded: Studies on Tiotropium in Patients with COPD; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.kearon1998 | 0 | excluded: Studies on the Accuracy of Venous Ultrasonography for the Diagnosis of Deep Venous Thrombosis; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.knapp2017 | 0 | excluded: schizophrenia versus healthy controls; task/difficulty and overlapping group IDs describe dependent outcomes, not alternative treatments |
| metadat | dat.konstantopoulos2011 | 0 | excluded: Studies on the Effects of Modified School Calendars on Student Achievement; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.landenberger2005 | 0 | excluded: CBT versus control; intervention-component indicators do not identify alternative study arms for an NMA |
| metadat | dat.laopaiboon2015 | 6 | included: explicit treatment identities and contrast/arm outcome data; full network plus two-arm subset where needed |
| metadat | dat.lau1992 | 0 | excluded: Studies on Intravenous Streptokinase for Acute Myocardial Infarction; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.lee2004 | 0 | excluded: Studies on Acupoint P6 Stimulation for Preventing Nausea; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.lehmann2018 | 0 | excluded: red-versus-control experiments with mixed designs and repeated samples; Color_Control can suggest a color network but no documented network/study covariance construction is supplied; excluded as a non-network collection, not claimed numerically validated |
| metadat | dat.li2007 | 0 | excluded: Studies on the Effectiveness of Intravenous Magnesium in Acute Myocardial Infarction; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.lim2014 | 0 | excluded: Studies on the Association Between Maternal Size, Offspring Size, and Number of Offsprings; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.linde2005 | 6 | included: explicit treatment identities and contrast/arm outcome data; full network plus two-arm subset where needed |
| metadat | dat.linde2015 | 60 | included: explicit treatment identities and contrast/arm outcome data; full network plus two-arm subset where needed |
| metadat | dat.linde2016 | 12 | included: explicit treatment identities and contrast/arm outcome data; full network plus two-arm subset where needed |
| metadat | dat.lloyd2010 | 0 | excluded: Studies on Anti-TNF-alpha Inhibitors in Rheumatoid Arthritis; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.lopez2019 | 6 | included: explicit treatment identities and contrast/arm outcome data; full network plus two-arm subset where needed |
| metadat | dat.maire2019 | 0 | excluded: Studies on Temporal Trends in Fish Community Structures in French Rivers; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.mccurdy2020 | 0 | excluded: generation versus reading experiments; multiple conditions/outcomes and dependent samples, not a documented treatment network |
| metadat | dat.mcdaniel1994 | 0 | excluded: Studies on the Validity of Employment Interviews; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.meeker2017 | 0 | excluded: Baseball Batting Averages; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.metap | 0 | excluded: collections of p-values; no treatment contrasts and sampling variances |
| metadat | dat.michael2013 | 0 | excluded: brain image versus no brain image only; two conditions |
| metadat | dat.molloy2014 | 0 | excluded: correlations; controls is a covariate-adjustment variable, not a comparator arm |
| metadat | dat.moore1998 | 0 | excluded: Trials on Non-Steroidal Anti-Inflammatory Drugs in Acute Pain; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.moura2021 | 0 | excluded: Studies on Assortative Mating; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.nakagawa2007 | 0 | excluded: Assessing the Function of House Sparrows' Bib Size Using a Flexible Meta-Analysis Method; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.nielweise2007 | 0 | excluded: Studies on Anti-Infective-Treated Central Venous Catheters for Prevention of Catheter-Related Bloodstream Infections; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.nielweise2008 | 0 | excluded: Studies on Anti-Infective-Treated Central Venous Catheters for Prevention of Catheter-Related Bloodstream Infections; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.nissen2007 | 12 | included: explicit treatment identities and contrast/arm outcome data; full network plus two-arm subset where needed |
| metadat | dat.normand1999 | 0 | excluded: Studies on the Length of Hospital Stay of Stroke Patients; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.obrien2003 | 0 | excluded: Studies on the Relationship Between BMI and Risk of Preeclampsia; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.pagliaro1992 | 12 | included: explicit treatment identities and contrast/arm outcome data; full network plus two-arm subset where needed |
| metadat | dat.pignon2000 | 0 | excluded: Studies on the Effectiveness of Locoregional Treatment plus Chemotherapy for Head and Neck Squamous-Cell Carcinoma; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.poole2003 | 0 | excluded: Trials on Mucolytic Agents in Chronic Bronchitis or Chronic Obstructive Pulmonary Disease; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.pritz1997 | 0 | excluded: Studies on the Effectiveness of Hyperdynamic Therapy for Treating Cerebral Vasospasm; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.quan2000 | 0 | excluded: Studies on Pharmacotherapy for Hypertension; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.raudenbush1985 | 0 | excluded: Studies on Assessing the Effects of Teacher Expectations on Pupil IQ; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.riley2003 | 0 | excluded: Studies on MYC-N as a Prognostic Marker for Neuroblastoma; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.rivera2025 | 0 | excluded: Comparison of Two Diagnostic Tests for the Detection of Temporomandibular Disorders; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.roever2022 | 0 | excluded: single-arm dose-toxicity data without within-study randomized treatment comparisons |
| metadat | dat.senn2013 | 12 | included: explicit treatment identities and contrast/arm outcome data; full network plus two-arm subset where needed |
| metadat | dat.spooner2002 | 0 | excluded: nedocromil versus placebo only; agegroup is a moderator, not a treatment arm |
| metadat | dat.steurer2006 | 0 | excluded: Trials on Single-Agent Purine Analogues for the Treatment of Chronic Lymphocytic Leukaemia; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.stowe2010 | 12 | included: explicit treatment identities and contrast/arm outcome data; full network plus two-arm subset where needed |
| metadat | dat.tannersmith2016 | 0 | excluded: Studies on the Relationship between School Motivation and Criminal Behavior; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.thompson1999 | 0 | excluded: cholesterol-lowering intervention versus control only; cholr is a continuous moderator |
| metadat | dat.tian2009 | 12 | included: explicit treatment identities and contrast/arm outcome data; full network plus two-arm subset where needed |
| metadat | dat.ursino2021 | 0 | excluded: single-arm dose-toxicity data without within-study randomized treatment comparisons |
| metadat | dat.vanhowe1999 | 0 | excluded: Studies on the Association between Circumcision and HIV Infection; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
| metadat | dat.viechtbauer2021 | 0 | excluded: hypothetical treatment-versus-control model-checking examples; dose is a continuous moderator, not a documented multi-treatment network |
| metadat | dat.white2020 | 0 | excluded: correlations between signals and quality; control/exp_obs are study-design moderators, not treatment alternatives |
| metadat | dat.woods2010 | 12 | included: explicit treatment identities and contrast/arm outcome data; full network plus two-arm subset where needed |
| metadat | dat.yusuf1985 | 0 | excluded: Studies of Beta Blockers During and After Myocardial Infarction; installed schema has no multi-treatment arm identities or labeled treatment-pair network with compatible outcomes |
