library(methods)
library(grid)
library(bcp)
library("TTR")

remove_NA <- function(ts)
{
	ts_without_NA <- c()
	for(i in ts)
		if(!is.na(i))
			ts_without_NA <- c(ts_without_NA, i)
	return(ts_without_NA)
}

df <- read.csv("./input/2015_12/NHODTCSRV04/64:66:B3:A6:B5:2E.csv", header = T, sep = ",")

ts <- df[,3]
ts_sma <- remove_NA(SMA(ts, n = 10))

ts_bcp <- bcp(ts_sma)
plot(ts_bcp)
