library(changepoint)

args <- commandArgs(trailingOnly = TRUE)
in_path <- args[1]
out_path <- args[2]
strdate_start <- args[3]
strdate_end <- args[4] 
pen <- as.numeric(args[5])
distr_type <- args[6]
min_seg_len <- as.numeric(args[7])

print(in_path)
print(out_path)
print(strdate_start)
print(strdate_end)
print(pen)
print(distr_type)
print(min_seg_len)

df <- read.csv(in_path, header=T, sep=",")

epoch_start <- as.numeric(as.POSIXct(strdate_start))
epoch_end <- as.numeric(as.POSIXct(strdate_end)) + 24*60*60 #include last day

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

changepoint <- cpt.meanvar(ts, penalty="Manual", 
                           method="PELT", pen.value=pen, test.stat=distr_type, 
                           minseglen=min_seg_len)
#check slot names: slotNames(changepoint)
#plot(changepoint)

write("id,dt", out_path)
for(cp in slot(changepoint, "cpts")) 
    write(paste(cp - 1, df[cp, "dt"], sep=","), out_path, append=T)
