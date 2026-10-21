source("r_session.R")
options(width=160)
G <- function(x,n) x[[n,exact=TRUE]]
PW <- function(...) {
 args<-list(...)
 p<-do.call(meta::pairwise,c(args,list(data=d)))
 missing_ids<-setdiff(as.character(G(args,"studlab")),as.character(G(p,"studlab")))
 for(id in missing_ids) rowledger[[length(rowledger)+1]] <<- list(package=pkg,dataset=nm,study=id,recipe=label,reason="meta::pairwise returned no contrasts (missing arm outcomes or inadequate treatment arms)")
 p
}
wide_binary <- function(a,b,e1,n1,e2,n2,id,sm) {
 z<-metafor::escalc(measure=sm,ai=e1,n1i=n1,ci=e2,n2i=n2,add=.5,to="only0",drop00=FALSE)
 data.frame(treat1=a,treat2=b,TE=G(z,"yi"),seTE=sqrt(G(z,"vi")),studlab=id)
}
inventory <- jsonlite::fromJSON("inventory.json",simplifyVector=FALSE)
corpus<-list(); ledger<-list(); attempts<-list(); rowledger<-list()
add <- function(pw, pkg, nm, outcome, measure, recipe) {
 d<-data.frame(A=as.character(G(pw,"treat1")),B=as.character(G(pw,"treat2")),te=G(pw,"TE"),se=G(pw,"seTE"),study=as.character(G(pw,"studlab")),source=seq_len(nrow(pw)),stringsAsFactors=FALSE)
 valid<-is.finite(d[["te"]]) & is.finite(d[["se"]]) & d[["se"]]>0 & !is.na(d[["A"]]) & !is.na(d[["B"]]) & d[["A"]]!=d[["B"]]
 for(i in which(!valid)) rowledger[[length(rowledger)+1]] <<- list(package=pkg,dataset=nm,outcome=outcome,measure=measure,pairwise_row=i,reason="missing/nonfinite effect or SE, nonpositive SE, missing/identical treatment")
 d<-d[valid,,drop=FALSE]
 if(!nrow(d)) return(invisible(NULL))
 # A repeated study identifier is never converted into independent studies.
 arms<-lapply(split(seq_len(nrow(d)),d[["study"]]),function(i) unique(c(d[["A"]][i],d[["B"]][i])))
 multi<-names(arms)[lengths(arms)>2]
 subsets<-list(full=d)
 if(length(multi)) subsets[["two-arm-only"]]<-d[!d[["study"]]%in%multi,,drop=FALSE]
 for(sub in names(subsets)) {
  dd<-subsets[[sub]]
  if(!nrow(dd)) next
  rows<-lapply(seq_len(nrow(dd)),function(i)as.list(dd[i,,drop=FALSE]))
  for(model in c("FE","DL","PM")) {
   key<-paste(pkg,nm,outcome,measure,sub,model,sep="::")
   corpus[[length(corpus)+1]] <<- list(key=key,package=pkg,dataset=nm,outcome=outcome,measure=measure,subset=sub,model=model,recipe=recipe,rows=rows,multiarm_studies=as.list(if(sub=="full")multi else character()))
  }
 }
}
for (item in inventory) {
 pkg<-G(item,"package"); nm<-G(item,"dataset"); short<-tolower(sub("^dat[.]","",nm)); e<-new.env(); data(list=nm,package=pkg,envir=e); d<-get(nm,e)
 before<-length(corpus); recipes<-list()
 addrecipe<-function(label,fun) recipes[[label]] <<- fun
 # Long-format network datasets. Every binary endpoint uses both scales
 # supported by the page's bus; continuous raw arms use MD and SMD.
 long<-switch(short,
  baker2009=c("study","treatment","exac","total"),
  dogliotti2014=c("study","treatment","stroke","total"),
  dong2013=c("id","treatment","death","randomized"),
  gurusamy2011=c("study","treatment","death","n"),
  woods2010=c("author","treatment","r","N"),
  hasselblad1998=c("study","trt","xi","ni"),
  pagliaro1992=c("study","trt","xi","ni"),
  linde2016=if(pkg=="metadat")c("id","int","resp","n") else NULL,
  NULL)
 if(!is.null(long)) for(sm in c("OR","RR")) local({v<-long; measure<-sm; addrecipe(paste(v[3],sm),function(){p<-PW(treat=G(d,v[2]),event=G(d,v[3]),n=G(d,v[4]),studlab=G(d,v[1]),sm=measure,allstudies=TRUE,incr=0.5,method.incr="only0");add(p,pkg,nm,v[3],measure,paste("meta::pairwise long",paste(v,collapse=","),"allstudies=TRUE, incr=.5 only0"))})})
 if(short %in% c("franchini2012","parkinson","stowe2010")) for(sm in c("MD","SMD")) local({measure<-sm; addrecipe(sm,function(){tp<-if(short=="stowe2010")"t" else "Treatment"; id<-if(short=="stowe2010")"id" else "Study"; cols<-function(pre)lapply(paste0(pre,1:3),function(n)G(d,n));p<-PW(treat=cols(tp),mean=cols("y"),sd=cols("sd"),n=cols("n"),studlab=G(d,id),sm=measure);add(p,pkg,nm,"change",measure,"meta::pairwise wide three-arm means/SD/n")})})
 if(short=="linde2015") for(ep in c("resp","remi","loss","loss.ae","ae")) for(sm in c("OR","RR")) local({out<-ep; measure<-sm; addrecipe(paste(ep,sm),function(){cols<-function(pre)lapply(paste0(pre,1:3),function(n)G(d,n));p<-PW(treat=cols("treatment"),event=cols(out),n=cols("n"),studlab=G(d,"id"),sm=measure,allstudies=TRUE,incr=.5,method.incr="only0");add(p,pkg,nm,out,measure,"meta::pairwise wide endpoint, allstudies=TRUE, incr=.5 only0")})})
 if(short=="smokingcessation") for(sm in c("OR","RR")) local({measure<-sm; addrecipe(sm,function(){cols<-function(pre)lapply(paste0(pre,1:3),function(n)G(d,n));p<-PW(treat=cols("treat"),event=cols("event"),n=cols("n"),studlab=seq_len(nrow(d)),sm=measure,allstudies=TRUE,incr=.5,method.incr="only0");add(p,pkg,nm,"cessation",measure,"meta::pairwise wide three-arm binary")})})
 if(short=="dietaryfat") addrecipe("IRR",function(){cols<-function(pre)lapply(paste0(pre,1:3),function(n)G(d,n));p<-PW(treat=cols("treat"),event=cols("d"),time=cols("years"),studlab=G(d,"ID"),sm="IRR");add(p,pkg,nm,"death","IRR","meta::pairwise incidence rates; log IRR from deaths/person-years")})
 if(short=="senn2013") {
  if(pkg=="netmeta") addrecipe("stored",function(){p<-data.frame(treat1=G(d,"treat1"),treat2=G(d,"treat2"),TE=G(d,"TE"),seTE=G(d,"seTE"),studlab=G(d,"studlab"));add(p,pkg,nm,"stored","MD","stored TE and seTE; original studlab preserved")})
  else for(sm in c("MD","SMD")) local({measure<-sm;addrecipe(sm,function(){p<-PW(treat=G(d,"treatment"),mean=G(d,"mi"),sd=G(d,"sdi"),n=G(d,"ni"),studlab=G(d,"study"),sm=measure);add(p,pkg,nm,"change",measure,"meta::pairwise long means/SD/n")})})
 }
 if(short=="linde2016" && pkg=="netmeta") addrecipe("stored",function(){p<-data.frame(treat1=G(d,"treat1"),treat2=G(d,"treat2"),TE=G(d,"lnOR"),seTE=G(d,"selnOR"),studlab=G(d,"id"));add(p,pkg,nm,"stored","OR","stored lnOR/selnOR; original id preserved")})
 if(short=="lopez2019") addrecipe("change",function(){
  groups<-split(seq_len(nrow(d)),G(d,"study")); pairs<-list()
  for(id in names(groups)) {
   ix<-groups[[id]]
   if(anyDuplicated(G(d,"treatment")[ix])) {rowledger[[length(rowledger)+1]]<<-list(package=pkg,dataset=nm,study=id,source_rows=as.list(ix),reason="multiple arms with identical treatment labels; combining arm standardized change scores requires an explicit aggregation assumption");next}
   for(j in combn(ix,2,simplify=FALSE)) pairs[[length(pairs)+1]]<-data.frame(treat1=G(d,"treatment")[j[1]],treat2=G(d,"treatment")[j[2]],TE=G(d,"diff")[j[1]]-G(d,"diff")[j[2]],seTE=sqrt(sum(G(d,"se")[j]^2)),studlab=id)
  }
  add(do.call(rbind,pairs),pkg,nm,"standardized-change","MD","documented diff1-diff2 and sqrt(se1^2+se2^2); same-treatment multiple-arm studies explicitly excluded")
 })
 # Additional explicit-treatment networks, including stars with zero loops.
 spec<-switch(short,
  axfors2021=list(A="hcq_cq",B="Control",e1="hcq_arm_event",n1="hcq_arm_total",e2="control_arm_event",n2="control_arm_total",id="acronym"),
  laopaiboon2015=list(A0="azithromycin",B="ctrl",e1="ai",n1="n1i",e2="ci",n2="n2i",id="author"),
  hart1999=list(A0="warfarin",B="compgrp",e1="x1i",n1="n1i",e2="x2i",n2="n2i",id="trial"),
  linde2005=list(A="prep",B0="placebo",e1="ai",n1="n1i",e2="ci",n2="n2i",id="id"),
  hartmannboyce2018=list(A="treatment",B0="control",e1="x.nrt",n1="n.nrt",e2="x.ctrl",n2="n.ctrl",id="study"),NULL)
 if(!is.null(spec)) for(sm in c("OR","RR")) local({measure<-sm;v<-spec;addrecipe(sm,function(){a<-if(!is.null(G(v,"A")))G(d,G(v,"A")) else rep(G(v,"A0"),nrow(d));b<-if(!is.null(G(v,"B")))G(d,G(v,"B")) else rep(G(v,"B0"),nrow(d));ids<-G(d,G(v,"id"));if(short=="laopaiboon2015")ids<-paste(ids,G(d,"year"));p<-wide_binary(a,b,G(d,G(v,"e1")),G(d,G(v,"n1")),G(d,G(v,"e2")),G(d,G(v,"n2")),ids,measure);add(p,pkg,nm,"event",measure,"documented active/comparator labels; metafor::escalc OR/RR add=.5 only0, drop00=FALSE; original study grouping (author/year for laopaiboon)")})})
 if(short %in% c("collins1985a","chiarito2020","nissen2007")) {
  eps<-switch(short,collins1985a=c("b","o","d"),chiarito2020=c("mi","stroke","death","vdeath"),nissen2007=c("infarction","death"))
  for(ep in eps) for(sm in c("OR","RR")) local({out<-ep;measure<-sm;addrecipe(paste(ep,sm),function(){
   if(short=="collins1985a") {a<-G(d,"trt");b<-G(d,"ctrl");e1<-G(d,paste0(out,".xti"));e2<-G(d,paste0(out,".xci"));n1<-G(d,"nti");n2<-G(d,"nci");id<-G(d,"id")}
   if(short=="chiarito2020") {a<-G(d,"p2y12");b<-rep("aspirin",nrow(d));e1<-G(d,paste0("p2y12.",out));e2<-G(d,paste0("aspirin.",out));n1<-G(d,"p2y12.total");n2<-G(d,"aspirin.total");id<-G(d,"study")}
   if(short=="nissen2007") {a<-G(d,"treatment");b<-G(d,"control");e1<-G(d,paste0("treat.",out));e2<-G(d,paste0("cont.",out));n1<-G(d,"treat.total");n2<-G(d,"cont.total");id<-G(d,"study")}
   p<-wide_binary(a,b,e1,n1,e2,n2,id,measure);add(p,pkg,nm,out,measure,"explicit treatment/comparator columns and endpoint; metafor::escalc OR/RR add=.5 only0, drop00=FALSE")
  })})
 }
 if(short=="tian2009") for(ep in c("deaths","infarcts")) for(sm in c("OR","RR")) local({out<-ep;measure<-sm;addrecipe(paste(ep,sm),function(){p<-PW(treat=G(d,"intervention"),event=G(d,out),n=G(d,"n"),studlab=G(d,"study"),sm=measure,allstudies=TRUE,incr=.5,method.incr="only0");add(p,pkg,nm,out,measure,"long intervention classes; original studies; meta::pairwise binary")})})
 if(short=="dagostino1998") for(ep in unique(G(d,"outcome"))) for(sm in if(grepl("goal",ep))c("OR","RR") else c("MD","SMD")) local({out<-ep;measure<-sm;addrecipe(paste(ep,sm),function(){
  dd<-d[G(d,"outcome")==out,,drop=FALSE]
  if(measure %in% c("OR","RR")) p<-wide_binary(G(dd,"drug"),rep("placebo",nrow(dd)),G(dd,"xt"),G(dd,"nt"),G(dd,"xc"),G(dd,"nc"),G(dd,"study"),measure)
  else {z<-metafor::escalc(measure=measure,m1i=G(dd,"mt"),sd1i=G(dd,"sdt"),n1i=G(dd,"nt"),m2i=G(dd,"mc"),sd2i=G(dd,"sdc"),n2i=G(dd,"nc"));p<-data.frame(treat1=G(dd,"drug"),treat2="placebo",TE=G(z,"yi"),seTE=sqrt(G(z,"vi")),studlab=G(dd,"study"))}
  add(p,pkg,nm,out,measure,"outcome/time-specific drug-versus-placebo star; metafor::escalc")
 })})
 for(label in names(recipes)) {
  warns<-character(); err<-NULL; n0<-length(corpus)
  tryCatch(withCallingHandlers(recipes[[label]](),warning=function(w){warns<<-c(warns,conditionMessage(w));invokeRestart("muffleWarning")}),error=function(e)err<<-conditionMessage(e))
  attempts[[length(attempts)+1]]<-list(package=pkg,dataset=nm,recipe=label,configurations=length(corpus)-n0,warnings=as.list(warns),error=err)
 }
 why<-if(length(corpus)>before) "included: explicit treatment identities and contrast/arm outcome data; full network plus two-arm subset where needed" else if(length(recipes)) "construction failed; see construction-attempts.json" else "excluded: no documented multi-treatment network with identifiable treatment pairs and compatible aggregate arm/contrast outcomes"
 ledger[[length(ledger)+1]]<-list(package=pkg,dataset=nm,title=G(item,"title"),columns=G(item,"columns"),configurations=length(corpus)-before,reason=why)
}
write_json17(corpus,"corpus.json");write_json17(ledger,"dataset-ledger.json");write_json17(attempts,"construction-attempts.json");write_json17(rowledger,"row-exclusions.json")
cat(length(corpus),"configurations from",sum(vapply(ledger,function(x)G(x,"configurations")>0,logical(1))),"datasets;",length(rowledger),"invalid pairwise rows excluded\n")
