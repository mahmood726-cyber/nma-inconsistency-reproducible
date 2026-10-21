source("r_session.R")
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
write_json17(fixtures,"bus-reference.json")
cat(length(fixtures),"bus transformation fixtures written\n")
