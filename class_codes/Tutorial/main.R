setwd(".")
dir.create("./plots", showWarnings = FALSE, recursive = TRUE)
fl1 <- "./Dataset/CompanyAge.txt"
compage <- read.table(file = fl1)
# compage

compAgeTS <- ts(compage)
pdf("./plots/CompanyAge.pdf")
plot.ts(compAgeTS)
dev.off()

fl2 <- "./Dataset/StartupMonth.txt"
startupMon <- read.table(file = fl2)
startupMonTs <- ts(startupMon, frequency=12, start=c(1946,1))
pdf("./plots/StartupMonth.pdf")
plot.ts(startupMonTs)
dev.off()

fl3 <- "./Dataset/MonSales.txt"
monsal <- read.table(file = fl3)
monSaleTS <- ts(monsal, frequency=12, start=c(1987,1))
pdf("./plots/MonSales.pdf")
plot.ts(monSaleTS)
dev.off()
longmonSaleTS <- log(monSaleTS)
pdf("./plots/MonSalesLog.pdf")
plot.ts(longmonSaleTS)
dev.off()


library("TTR")
compAgeTSSMA3 <- SMA(compAgeTS)