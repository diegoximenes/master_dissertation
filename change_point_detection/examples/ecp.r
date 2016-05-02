library(Rcpp)
library(ecp)

df <- read.csv("./input/2015_12/NHODTCSRV04/64:66:B3:A6:B5:2E.csv", header = T, sep = ",")

ts <- df[,3]
mat <- matrix(ts, nrow = length(ts), ncol = 1)

print("cp3o")
ecp <- e.cp3o(mat)
print(c("estimates=", ecp$estimates))

print("divisive")
ecp <- e.divisive(mat)
print(c("estimates=", ecp$estimates))

print("agglo")
ecp <- e.agglo(mat)
print(c("estimates=", ecp$estimates))

