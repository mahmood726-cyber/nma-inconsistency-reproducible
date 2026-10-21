# Generated from bench/focused.R and bench/bus_reference.R with explicit CORPUS/OUT.
# The documentation snapshot write is omitted; statistical code is unchanged.
z<-c(seq(-10,10,by=.125),1.959963984540054,0,1e-12)
write_json17(lapply(z,function(x)list(z=x,p=2*pnorm(-abs(x)))),file.path(OUT,"normal-reference.json"))
# Demonstrate why flattening a genuine multi-arm network is not numerical parity.
cs<-jsonlite::fromJSON(CORPUS,simplifyVector=FALSE)
G<-function(x,n)x[[n,exact=TRUE]]
out<-list()
for(nm in c("Senn2013","smokingcessation","Baker2009")) {
 c<-Filter(function(x)G(x,"package")=="netmeta"&&G(x,"dataset")==nm&&G(x,"subset")=="full"&&G(x,"model")=="FE",cs)[[1]]
 d<-do.call(rbind,lapply(G(c,"rows"),as.data.frame,stringsAsFactors=FALSE))
 fits<-list()
 for(mode in c("true-studies","flattened")) {
  m<-netmeta(TE=G(d,"te"),seTE=G(d,"se"),treat1=G(d,"A"),treat2=G(d,"B"),studlab=if(mode=="flattened")seq_len(nrow(d)) else G(d,"study"),common=TRUE,random=FALSE,method.tau="DL",sm="MD",tau.preset=0,warn=FALSE)
  dec<-decomp.design(m,warn=FALSE)[["Q.decomp",exact=TRUE]]
  s<-netsplit(m,method="Back-calculation")
  fits[[mode]]<-list(Q=G(m,"Q"),df=G(m,"df.Q"),dbt=list(Q=G(dec,"Q")[3],df=G(dec,"df")[3],p=G(dec,"pval")[3]),split=G(s,"compare.common"))
 }
 out[[length(out)+1]]<-list(key=G(c,"key"),fits=fits)
}
write_json17(out,file.path(OUT,"multiarm-diagnostic.json"))
cat(length(z),"normal p-value oracles;",length(out),"multi-arm native-versus-flattened diagnostics\n")
fixtures<-list()
for(zero in c(FALSE,TRUE)) for(sm in c("OR","RR","MD","SMD")) {
 studies<-list(
  list(id="s1",arms=list(list(treatment="A",events=if(zero)0 else 3,n=8,mean=2,sd=1.2),list(treatment="B",events=4,n=9,mean=3,sd=1.7))),
  list(id="s2",arms=list(list(treatment="B",events=6,n=10,mean=1,sd=.8),list(treatment="C",events=if(zero)7 else 3,n=7,mean=2.2,sd=1.1))),
  list(id="s3",arms=list(list(treatment="A",events=2,n=11,mean=3.4,sd=1.9),list(treatment="C",events=if(zero)0 else 1,n=13,mean=.8,sd=2.2))))
 rows<-lapply(studies,function(s){a<-s[["arms",exact=TRUE]][[1]];b<-s[["arms",exact=TRUE]][[2]]
  if(sm%in%c("OR","RR")) z<-metafor::escalc(measure=sm,ai=a[["events",exact=TRUE]],n1i=a[["n",exact=TRUE]],ci=b[["events",exact=TRUE]],n2i=b[["n",exact=TRUE]],add=.5,to="only0",drop00=FALSE)
  else z<-metafor::escalc(measure=sm,m1i=a[["mean",exact=TRUE]],sd1i=a[["sd",exact=TRUE]],n1i=a[["n",exact=TRUE]],m2i=b[["mean",exact=TRUE]],sd2i=b[["sd",exact=TRUE]],n2i=b[["n",exact=TRUE]],vtype="LS")
  list(study=s[["id",exact=TRUE]],A=a[["treatment",exact=TRUE]],B=b[["treatment",exact=TRUE]],te=z[["yi",exact=TRUE]][1],se=sqrt(z[["vi",exact=TRUE]][1]))})
 fixtures[[length(fixtures)+1]]<-list(key=paste(sm,zero,sep="::"),measure=sm,studies=studies,rows=rows)
}
write_json17(fixtures,file.path(OUT,"bus-reference.json"))
cat(length(fixtures),"bus transformation fixtures written\n")
