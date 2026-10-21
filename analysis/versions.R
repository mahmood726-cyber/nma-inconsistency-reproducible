# Exact versions recorded by every R log of the validation bundle (bench/*.log). Any difference refuses the run.
REQUIRED <- c(R='4.6.0', netmeta='3.7.0', meta='8.5.0', metadat='1.6.0', metafor='5.2.1', jsonlite='2.0.0')
installed_versions <- function(pkgs=names(REQUIRED)[-1]) {
 c(R=as.character(getRversion()), vapply(pkgs, function(p) tryCatch(as.character(packageVersion(p)), error=function(e) 'MISSING'), ''))
}
check_versions <- function(actual, expected=REQUIRED) {
 if(!identical(actual, expected)) stop('Wrong R/package versions. Required: ', paste(names(expected), expected, collapse=', '),
  '. Found: ', paste(names(actual), actual, collapse=', '), call.=FALSE)
 invisible(TRUE)
}
