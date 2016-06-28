library(changepoint)

args <- commandArgs(trailingOnly=TRUE)
in_path <- args[1]
out_path <- args[2]
pen <- as.numeric(args[3])
distr_type <- args[4]
min_seg_len <- as.numeric(args[5])

print(in_path)
print(out_path)
print(pen)
print(distr_type)
print(min_seg_len)

df <- read.csv(in_path, header=T, sep=",")
ts <- df[,1]

changepoint <- cpt.meanvar(ts, penalty="Manual", 
                           method="PELT", pen.value=pen, test.stat=distr_type, 
                           minseglen=min_seg_len)
#check slot names: slotNames(changepoint)
#plot(changepoint)

write("id,dt", out_path)
for(cp in slot(changepoint, "cpts")) 
    write(paste(cp - 1, df[cp, "dt"], sep=","), out_path, append=T)
