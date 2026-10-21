# Plus layer of the validation archive: leave-one-study-out (LOO) inconsistency reference and app replay.
# Run from the archive root:  Rscript plus/validate-plus.R     (validate.R also calls it after the v1 checks)
# 1. refuses unless R and package versions equal the recorded ones (same fail-closed check as validate.R);
# 2. SHA-256 checks every plus evidence file against plus/MANIFEST-plus.json and plus/app/SOURCE.json;
# 3. refits in native R a SEEDED SUBSET of the 153 plus configurations (every study removed in turn) with the
#    archived oracle plus/app/nma-inconsistency/validate/generate-plus.R, and requires every quantity of every
#    fresh drop-fit to equal plus/reference.json within 1e-12 relative (strings, counts and statuses exact).
#    The full refit takes about 7 hours (25,600 s summed); the subset is the configurations whose removals
#    include a refusal (disconnected network) plus 2 loop configurations per model drawn with set.seed(20261020)
#    and the first no-loop configuration per model. PLUS_FULL=1 refits all 153.
# 4. executes the archived page engine + plus replay in Node.js (plus/app/.../derive-plus-checks.cjs) against the
#    pinned references and requires "PLUS NODE REPLAY N/N" with N = the pinned check count.
# Prints N/N lines and stops (non-zero exit) on any failure. PLUS_PLANT=1 plants a defect (one reference Q
# scaled by 1 + 1e-6) to show that step 3 fails.
local({
start <- proc.time()[['elapsed']]
source('analysis/versions.R')
actual <- installed_versions(); print(actual); check_versions(actual)
cat('Plus version check PASS\n')
G <- function(x, n) x[[n, exact = TRUE]]
app <- 'plus/app/nma-inconsistency'
src <- jsonlite::fromJSON('plus/app/SOURCE.json', simplifyVector = FALSE)
files <- vapply(G(src, 'files'), function(f) G(f, 'path'), '')
want <- vapply(G(src, 'files'), function(f) G(f, 'sha256'), '')
got <- unname(tools::sha256sum(file.path('plus/app', files)))
if (!identical(got, want)) stop('plus/app SHA-256 mismatch: ', paste(head(files[got != want], 3), collapse = ', '))
man <- jsonlite::fromJSON(file.path(app, 'validate/MANIFEST-plus.json'), simplifyVector = FALSE)
for (f in G(man, 'files')) {
 h <- unname(tools::sha256sum(file.path(app, G(f, 'path'))))
 if (!identical(h, G(f, 'sha256'))) stop('Plus manifest SHA-256 mismatch: ', G(f, 'path'))
}
cat(sprintf('Plus SHA-256 checks PASS: %d app files, %d manifest files\n', length(files), length(G(man, 'files'))))
corpus <- jsonlite::fromJSON(file.path(app, 'validate/plus/corpus.json'), simplifyVector = FALSE)
ref <- jsonlite::fromJSON(file.path(app, 'validate/plus/reference.json'), simplifyVector = FALSE)
cases <- G(ref, 'cases')
stopifnot(length(corpus) == 153L, length(cases) == 153L,
          identical(vapply(corpus, function(c) G(c, 'key'), ''), vapply(cases, function(c) G(c, 'key'), '')))
models <- vapply(corpus, function(c) G(c, 'model'), ''); loops <- vapply(corpus, function(c) isTRUE(G(c, 'loops')), NA)
refused <- vapply(cases, function(x) any(vapply(G(x, 'drops'), function(d) G(G(d, 'fit'), 'status') != 'ok', NA)), NA)
if (Sys.getenv('PLUS_FULL', '0') == '1') pick <- seq_along(corpus) else {
 set.seed(20261020)
 pick <- which(refused)
 for (m in c('FE', 'DL', 'PM')) {
  pool <- setdiff(which(models == m & loops), pick)
  pick <- c(pick, pool[sample.int(length(pool), 2L)], which(models == m & !loops)[1])
 }
 pick <- sort(unique(pick))
}
cat('Plus subset (corpus positions):', pick, '\n')
work <- '.validate-work/plus'
if (file.exists(work)) stop('Existing ', work, ' refused (stale-result guard)')
dir.create(work, recursive = TRUE)
sub <- corpus[pick]
# Same 17-significant-digit encoder as the oracle (generate-plus.R), so the subset corpus round-trips exactly.
enc <- function(v) {
 if (is.null(v)) return('null')
 if (is.list(v)) {
  z <- vapply(v, enc, character(1))
  if (!is.null(names(v))) return(paste0('{', paste(paste0(vapply(names(v), function(s) encodeString(s, quote = '"'), ''), ':', z), collapse = ','), '}'))
  return(paste0('[', paste(z, collapse = ','), ']'))
 }
 atom <- function(a) if (is.na(a)) 'null' else if (is.numeric(a)) sprintf('%.17g', a) else if (is.logical(a)) (if (a) 'true' else 'false') else encodeString(as.character(a), quote = '"')
 z <- vapply(v, atom, character(1)); if (length(z) == 1) z else paste0('[', paste(z, collapse = ','), ']')
}
writeLines(enc(sub), file.path(work, 'corpus.json'), useBytes = TRUE)
back <- jsonlite::fromJSON(file.path(work, 'corpus.json'), simplifyVector = FALSE)
if (!identical(back, sub)) stop('Subset corpus did not round-trip exactly')
rscript <- file.path(R.home('bin'), 'Rscript')
log <- file.path(work, 'generate-plus.log')
status <- system2(rscript, c('--vanilla', file.path(app, 'validate/generate-plus.R'), file.path(work, 'corpus.json'),
                             'results/reference', file.path(work, 'out')), stdout = log, stderr = log)
cat(readLines(log), sep = '\n')
if (!identical(as.integer(status), 0L)) stop('generate-plus.R failed (exit status ', status, ')')
# Compare fresh with archived: every leaf; numbers within 1e-12 relative to max(1, |archived|).
n <- 0L; ok <- 0L; worst <- 0; bad <- character()
cmp <- function(a, b, path) {
 if (is.list(b)) {
  if (!is.list(a) || !identical(names(a), names(b)) || length(a) != length(b)) { n <<- n + 1L; bad <<- c(bad, paste(path, 'structure')); return() }
  for (i in seq_along(b)) cmp(a[[i]], b[[i]], paste0(path, '/', if (is.null(names(b))) i else names(b)[i]))
 } else {
  n <<- n + 1L
  if (is.numeric(b) && is.numeric(a) && length(a) == 1L && length(b) == 1L && !is.na(a) && !is.na(b)) {
   d <- abs(a - b) / max(1, abs(b)); worst <<- max(worst, d)
   if (d <= 1e-12) ok <<- ok + 1L else bad <<- c(bad, sprintf('%s %.17g vs %.17g', path, a, b))
  } else if (identical(a, b)) ok <<- ok + 1L else bad <<- c(bad, paste(path, 'differs'))
 }
}
plant <- Sys.getenv('PLUS_PLANT', '0') == '1'
for (j in seq_along(pick)) {
 fresh <- jsonlite::fromJSON(file.path(work, 'out', sprintf('%05d.json', j)), simplifyVector = FALSE)
 arch <- cases[[pick[j]]]
 if (plant && j == 1L) { arch$full$Q <- arch$full$Q * (1 + 1e-6); cat('PLANTED: archived full Q of', G(arch, 'key'), 'scaled by 1 + 1e-6\n') }
 stopifnot(identical(G(fresh, 'key'), G(arch, 'key')))
 for (k in c('model', 'full_check', 'full', 'drops')) cmp(G(fresh, k), G(arch, k), paste0(G(arch, 'key'), '/', k))
}
drops <- sum(vapply(cases[pick], function(x) length(G(x, 'drops')), 0L))
cat(sprintf('Plus R refit (%s): %d configurations / %d drop-fits; max relative difference %.3g\n',
            if (length(pick) == 153L) 'all' else 'seeded subset', length(pick), drops, worst))
cat(sprintf('%d/%d plus reference quantities reproduced\n', ok, n))
if (ok != n) { cat(head(bad, 20), sep = '\n'); stop('Plus reference not reproduced') }
node <- Sys.which('node')
if (!nzchar(node)) stop('Node.js is required for the plus app replay (step 4); none found on PATH')
out <- system2(node, file.path(app, 'validate/derive-plus-checks.cjs'), stdout = TRUE, stderr = TRUE)
writeLines(out, file.path(work, 'node-replay.log'))
line <- grep('^PLUS NODE REPLAY ', out, value = TRUE)
expect <- sprintf('PLUS NODE REPLAY %d/%d ', G(man, 'checks'), G(man, 'checks'))
cat(line, '\n')
if (length(line) != 1L || !startsWith(line, expect)) stop('Plus app replay did not pass: expected ', expect)
cat(sprintf('Plus runtime: %.1f seconds\n', proc.time()[['elapsed']] - start))
cat(sprintf('%d/%d plus app replay checks pass\n', G(man, 'checks'), G(man, 'checks')))
})
