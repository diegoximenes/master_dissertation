library(methods)
library(cpm)

df <- read.csv("./input/2015_12/NHODTCSRV04/64:66:B3:A6:B5:2E.csv", header = T, sep = ",")

ts <- df[,3]

png("plot_cpm.png")

cpm_detection <- detectChangePointBatch(ts, cpmType="GLR")
#cpm_detection <- detectChangePoint(ts, cpmType="GLR")
plot.ts(ts)
if(cpm_detection$changeDetected) abline(v = cpm_detection$changePoint, col = "red")

dev.off()
