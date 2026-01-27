# r/cv_calc.R

df <- read.csv(file("stdin"), row.names = 1, check.names = FALSE)

cv_values <- apply(df, 1, function(x) {
  x <- as.numeric(x)   # force numeric

  mu <- mean(x, na.rm = TRUE)
  sigma <- sd(x, na.rm = TRUE)

  # Handle NA or zero mean safely
  if (is.na(mu) || mu == 0) {
    return(NA)
  } else {
    return(sigma / mu)
  }
})

out <- data.frame(CV = cv_values)
write.csv(out, stdout())


