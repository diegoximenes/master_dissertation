library(changepoint)

#args = commandArgs(trailingOnly = TRUE)
#in_path <- args[1]
#out_path <- args[2]
#strdate_start <- args[3]
#strdate_end <- args[4] 

in_path = "../input/2016_05/SNEDTCPROB01/64:66:B3:4F:FE:CE.csv"
out_path <- "cp.csv"
strdate_start <- "2016-05-11"
strdate_end <- "2016-05-21" #not included in range

df <- read.csv(in_path, header=T, sep=",")

epoch_start <- as.numeric(as.POSIXct(strdate_start))
epoch_end <- as.numeric(as.POSIXct(strdate_end))

#csv file is already sorted by dt
ts <- c()
for(i in 1:nrow(df))
{
    strdt <- as.character(df[i, "dt"])
    strdate <- unlist(strsplit(strdt, " "))[1]
    epoch <- as.numeric(as.POSIXct(strdate))
    if((epoch >= epoch_start) && (epoch < epoch_end)) 
        ts <- c(ts, df[i, "loss"])
}

#changepoint <- cpt.meanvar(ts, penalty="SIC", method="SegNeigh", Q=10)
changepoint <- cpt.meanvar(ts, pen.value=200, penalty="Manual", 
                           method="SegNeigh", Q=10)
#check slot names: slotNames(changepoint)
plot(changepoint)

write("changepoint,datetime", out_path)
for(cp in slot(changepoint, "cpts")) 
    write(paste(cp, df[cp, "dt"], sep=","), out_path, append=T)
