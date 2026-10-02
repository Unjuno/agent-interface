cfg <- jsonlite::fromJSON("prereg.json")
for (seed in cfg$seeds) {
  set.seed(seed)
  x <- rexp(cfg$sample_size, rate = 1)
  writeLines(sprintf("%.17g", x), file.path("input", paste0(seed, ".txt")))
}
