source("r_session.R")
G<-function(x,n)x[[n,exact=TRUE]]
indirect_path<-function(A,B,pair) {
 keep<-!((A==pair[1]&B==pair[2])|(A==pair[2]&B==pair[1]));a<-A[keep];b<-B[keep];seen<-pair[1]
 repeat{new<-unique(c(seen,b[a%in%seen],a[b%in%seen]));if(length(new)==length(seen))break;seen<-new}
 pair[2]%in%seen
}
cs<-jsonlite::fromJSON("corpus.json",simplifyVector=FALSE)
dir.create("reference",showWarnings=FALSE)
args<-commandArgs(TRUE); start<-if(length(args))as.integer(args[1]) else 1L; step<-if(length(args)>1)as.integer(args[2]) else 1L
for(i in which((seq_along(cs)-1L)%/%3L%%step==start-1L)) {
 c<-cs[[i]]; key<-G(c,"key"); warnings<-character(); began<-proc.time()[["elapsed"]]
 existing<-sprintf("reference/%05d.json",i)
 if(file.exists(existing)) {
  prev<-jsonlite::fromJSON(existing,simplifyVector=FALSE)
  if(identical(G(prev,"key"),key) && (G(c,"model")!="PM" || identical(G(prev,"status"),"refused") || identical(G(prev,"pm_reference"),"uncentered package QE"))) {cat(i,"cached",key,"\n");next}
 }
 result<-tryCatch(withCallingHandlers({
  d<-do.call(rbind,lapply(G(c,"rows"),as.data.frame,stringsAsFactors=FALSE))
  A<-G(d,"A");B<-G(d,"B");te<-G(d,"te");se<-G(d,"se");study<-G(d,"study");model<-G(c,"model")
  tr<-sort(unique(c(A,B)),method="radix"); adjacency<-lapply(tr,function(t) unique(c(B[A==t],A[B==t])));names(adjacency)<-tr
  reached<-tr[1];repeat{nextset<-unique(c(reached,unlist(adjacency[reached])));if(length(nextset)==length(reached))break;reached<-nextset}
  reason<-if(nrow(d)<3)"At least 3 valid contrasts are required." else if(length(G(c,"multiarm_studies")))"Multi-arm studies are unsupported: correlated contrasts require study covariance." else if(anyDuplicated(study))"Repeated study IDs are unsupported: enter one independent contrast per study." else if(length(reached)<length(tr))"The treatment network is disconnected." else NULL
  if(!is.null(reason)) list(key=key,status="refused",reason=reason,scope="input-support gate; not a numerical netmeta success") else {
   tau<-0
   if(model=="PM") {
    X<-sapply(tr[-1],function(t)as.numeric(A==t)-as.numeric(B==t))
    if(nrow(d)>ncol(as.matrix(X))) {
     qe<-get(".QE.func",asNamespace("metafor"))
     f<-function(t2)qe(t2,Y=as.matrix(te),vi=se^2,X=as.matrix(X),k=nrow(d),objective=nrow(d)-ncol(as.matrix(X)))
     if(f(0)>0) {
      upper<-max(1,var(te));while(f(upper)>0)upper<-upper*2
      tau<-sqrt(uniroot(f,c(0,upper),tol=.Machine$double.eps^0.75,maxiter=1000)[["root",exact=TRUE]])
     }
    }
   }
   m<-netmeta(TE=te,seTE=se,treat1=A,treat2=B,studlab=study,sm="MD",reference.group=tr[1],common=TRUE,random=TRUE,method.tau="DL",tau.preset=if(model=="DL")NULL else tau,sep.trts=" ~~ ",warn=FALSE)
   tau<-if(model=="FE")0 else G(m,"tau")
   s<-netsplit(m,method="Back-calculation",tol.direct=0)
   suffix<-if(model=="FE")"common" else "random"
   direct<-G(s,paste0("direct.",suffix));indirect<-G(s,paste0("indirect.",suffix));cmp<-G(s,paste0("compare.",suffix))
   splits<-list(); exclusions<-list()
   for(j in seq_len(nrow(cmp))) {
    pair<-strsplit(G(cmp,"comparison")[j]," ~~ ",fixed=TRUE)[[1]]; ordered<-sort(pair,method="radix");sgn<-if(pair[1]==ordered[1])1 else -1
    name<-paste(ordered,collapse=" vs ")
    if(!is.finite(G(direct,"TE")[j]) || !indirect_path(A,B,ordered)) {exclusions[[length(exclusions)+1]]<-list(comparison=name,reason=if(!is.finite(G(direct,"TE")[j]))"no direct evidence" else "no independent indirect path");next}
    if(!is.finite(G(cmp,"TE")[j])) stop(paste("netmeta did not return an estimable graph-supported split:",name))
    splits[[length(splits)+1]]<-list(comparison=name,direct=list(mean=sgn*G(direct,"TE")[j],se=G(direct,"seTE")[j]),indirect=list(mean=sgn*G(indirect,"TE")[j],se=G(indirect,"seTE")[j]),diff=sgn*G(cmp,"TE")[j],seDiff=G(cmp,"seTE")[j],z=sgn*G(cmp,"statistic")[j],p=G(cmp,"p")[j],kDirect=sum((A==ordered[1]&B==ordered[2])|(A==ordered[2]&B==ordered[1])))
   }
   dec<-decomp.design(m,tau.preset=tau,warn=FALSE)
   q<-if(model=="FE")G(dec,"Q.decomp") else G(dec,"Q.inc.random.preset")
   if(is.null(q)) global<-list(Q=0,df=0,p=NA_real_) else {row<-match("Between designs",rownames(q));global<-list(Q=G(q,"Q")[row],df=G(q,"df")[row],p=G(q,"pval")[row])}
   if(!is.null(G(global,"df")) && G(global,"df")==0) {global[["Q"]]<-0;global[["p"]]<-NA_real_}
   estimates<-function(which) setNames(lapply(tr,function(t)list(est=G(m,paste0("TE.",which))[t,tr[1]],se=G(m,paste0("seTE.",which))[t,tr[1]])),tr)
   re<-estimates("random");fe<-estimates("common")
   beta<-vapply(re,function(z)G(z,"est"),numeric(1)); qr<-sum((te-(beta[A]-beta[B]))^2/(se^2+tau^2))
   list(key=key,status="ok",trts=as.list(tr),Q=G(m,"Q"),df=G(m,"df.Q"),tau2=tau^2,Qrandom=qr,estimates=fe,estimatesRandom=re,nodeSplit=splits,dbt=global,split_exclusions=exclusions,k=nrow(d),model=model)
  }
 },warning=function(w){warnings<<-c(warnings,conditionMessage(w));invokeRestart("muffleWarning")}),error=function(e)list(key=key,status="error",reason=conditionMessage(e)))
 result[["warnings"]]<-as.list(warnings);result[["seconds"]]<-proc.time()[["elapsed"]]-began
 result[["pm_reference"]]<-"uncentered package QE"
 write_json17(result,sprintf("reference/%05d.json",i))
 cat(i,key,G(result,"status"),if(!is.null(G(result,"reason")))G(result,"reason") else "","\n");flush.console()
}
cat("Reference shard complete",start,step,"\n")
