library(changepoint)

args = commandArgs(trailingOnly = TRUE)
in_file = args[1]
out_file = args[2]

#df <- read.csv("../input/2015_12/NHODTCSRV04/64:66:B3:A6:B5:2E.csv", header = T, sep = ",")
df <- read.csv(in_file, header = T, sep = ",")
ts <- df[,3]

#changepoint <- cpt.mean(ts, penalty = "AIC", method = "SegNeigh", Q = 10)
changepoint <- cpt.mean(ts, penalty = "AIC", method = "PELT", Q = 10)
#check slot names: slotNames(changepoint)
plot(changepoint)

write("changepoint,datetime", out_file)
for(cp in slot(changepoint, "cpts")) write(paste(cp, df[cp, 2], sep = ","), out_file, append = T)
