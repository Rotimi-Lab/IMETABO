#!/usr/bin/env Rscript

# Read CSV from stdin WITH header
input <- read.csv(
  file("stdin"),
  header = TRUE,
  check.names = FALSE,
  na.strings = c("", "NA")
)

# Keep numeric columns only
input <- input[, sapply(input, is.numeric), drop = FALSE]

# Compute means (ignore NA)
means <- colMeans(input, na.rm = TRUE)

# Keep only features with non-zero mean (CV undefined otherwise)
input <- input[, means != 0, drop = FALSE]
means <- means[means != 0]

# Compute coefficient of variation (CV = sd / mean)
cv <- apply(
  input,
  2,
  function(x) {
    sd(x, na.rm = TRUE) / mean(x, na.rm = TRUE)
  }
)

# Output tidy result
output <- data.frame(
  feature = names(cv),
  cv = as.numeric(cv)
)

# Write CSV to stdout
write.csv(output, row.names = FALSE)
