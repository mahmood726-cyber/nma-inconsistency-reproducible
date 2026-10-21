# One-command validation: Rscript validate.R   (run from the archive root)
# 1. refuses unless R and package versions equal those recorded in the validation bundle;
# 2. SHA-256 checks the complete source inventory (SOURCE_SHA256.json);
# 3. refits every one of the 540 configurations in R from data/corpus.json (no archived fit is reused);
# 4. captures the candidate primary/focused page outputs anew in Node, checks fresh R against
#    the archived reference, and compares candidate and historical-original outputs with fresh R.
#    Prints "N/N checks pass" only on success. Any failure exits nonzero.
# Set R_ENVIRON_USER to an empty file (NUL on Windows) so a user .Renviron cannot change the library paths;
# set R_LIBS_USER/R_LIBS to the libraries holding the exact versions and PYTHON to a Python 3 executable if
# `python` is not on PATH. No packages are installed and no network access is needed.
start <- proc.time()[['elapsed']]
source('analysis/versions.R')
cat('.libPaths():\n'); print(.libPaths())
cat(R.version.string, '\n')
actual <- installed_versions()
print(actual)
check_versions(actual)
cat('Version check PASS\n')
pins <- jsonlite::fromJSON('SOURCE_SHA256.json', simplifyVector=FALSE)
files <- list.files('.', recursive=TRUE, all.files=TRUE, no..=TRUE)
files <- files[!grepl('^(\\.git|\\.validate-work|\\.verify-[^/]*)/', files) & !grepl('(^|/)(__pycache__|\\.pytest_cache)/', files) &
               !(files %in% c('SOURCE_SHA256.json'))]
if(anyDuplicated(names(pins)) || !setequal(files, names(pins)) || length(files) != length(pins))
 stop('Source inventory mismatch: missing ', paste(head(setdiff(names(pins), files), 3), collapse=', '), '; extra ', paste(head(setdiff(files, names(pins)), 3), collapse=', '))
hashes <- tools::sha256sum(names(pins))
bad <- names(pins)[unname(hashes) != unlist(pins, use.names=FALSE)]
if(length(bad)) stop('Input SHA-256 mismatch: ', paste(head(bad, 5), collapse=', '))
cat(sprintf('Input SHA-256 checks PASS: %d files\n', length(pins)))
work <- '.validate-work'
if(file.exists(work)) stop('Existing .validate-work refused (stale-result guard); move it aside before a new full run')
dir.create(work)
suppressPackageStartupMessages(library(netmeta))
source('analysis/json17.R')
fit <- function(script, out) {
 env <- new.env(parent=globalenv()); env$CORPUS <- 'data/corpus.json'; env$OUT <- out
 t0 <- proc.time()[['elapsed']]; sys.source(script, envir=env, keep.source=FALSE)
 cat(sprintf('%s finished in %.1f seconds\n', script, proc.time()[['elapsed']] - t0)); flush.console()
}
fit('analysis/refit_reference.R', file.path(work, 'reference'))
fit('analysis/refit_focused.R', work)
python <- Sys.getenv('PYTHON', unset='python')
status <- system2(python, c('-B', 'analysis/capture_candidate.py', work))
if(!identical(as.integer(status), 0L)) stop('Candidate capture failed (exit status ', status, ')')
status <- system2(python, c('-B', 'analysis/run_checks.py', work))
if(!identical(as.integer(status), 0L)) stop('Archive comparison failed (analysis/run_checks.py exit status ', status, ')')
summary <- jsonlite::fromJSON(file.path(work, 'summary.json'), simplifyVector=FALSE)
cat(sprintf('Runtime: %.1f seconds\n', proc.time()[['elapsed']] - start))
cat(summary[['final_line', exact=TRUE]], '\n', sep='')

# Plus layer (leave-one-study-out panel, PR #160): see plus/README.md
source('plus/validate-plus.R')
