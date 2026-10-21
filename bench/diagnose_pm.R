source("r_session.R");G<-function(x,n)x[[n,exact=TRUE]]
c<-jsonlite::fromJSON("corpus.json",simplifyVector=FALSE)[[6]]
d<-do.call(rbind,lapply(G(c,"rows"),as.data.frame,stringsAsFactors=FALSE));A<-G(d,"A");B<-G(d,"B");te<-G(d,"te");se<-G(d,"se");tr<-sort(unique(c(A,B)),method="radix")
X<-sapply(tr[-1],function(t)as.numeric(A==t)-as.numeric(B==t))
pm<-metafor::rma(yi=te,vi=se^2,mods=X,intercept=FALSE,method="PM",control=list(threshold=1e-12,tol=.Machine$double.eps^0.75,maxiter=1000,tau2.max=max(100,100*var(te))))
cat("pm tau2",G(pm,"tau2"),"p",G(pm,"p"),"k",G(pm,"k"),"\n")
print(G(pm,"X"));print(X)
for(t in c(G(pm,"tau2"),.018163791725995027)) {
 fit<-lm.wfit(X,te,w=1/(se^2+t));cat("tau2",t,"Q",sum(G(fit,"residuals")^2/(se^2+t)),"\n")
}
writeLines(capture.output(print(get(".QE.func",asNamespace("metafor")))),"documentation/PM-QE-source.txt")
