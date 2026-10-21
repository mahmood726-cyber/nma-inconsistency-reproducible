source("r_session.R")
z<-c(seq(-10,10,by=.125),1.959963984540054,0,1e-12)
write_json17(lapply(z,function(x)list(z=x,p=2*pnorm(-abs(x)))),"normal-reference.json")
writeLines(capture.output(print(metafor::rma.uni)),"documentation/rma.uni-source.txt")
# Demonstrate why flattening a genuine multi-arm network is not numerical parity.
cs<-jsonlite::fromJSON("corpus.json",simplifyVector=FALSE)
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
write_json17(out,"multiarm-diagnostic.json")
cat(length(z),"normal p-value oracles;",length(out),"multi-arm native-versus-flattened diagnostics\n")
