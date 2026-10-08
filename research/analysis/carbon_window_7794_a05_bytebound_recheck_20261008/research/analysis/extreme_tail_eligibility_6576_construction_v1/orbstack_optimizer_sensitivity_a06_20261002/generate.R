seeds <- 65769931:65769936
for (seed in seeds) {
  set.seed(seed)
  x <- rexp(400, rate = 1)
  writeLines(sprintf("%.17g", x), file.path("input", paste0(seed, ".txt")))
}
