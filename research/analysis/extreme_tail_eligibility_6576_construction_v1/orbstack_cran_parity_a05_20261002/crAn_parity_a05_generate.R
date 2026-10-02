args <- commandArgs(trailingOnly = TRUE)
config <- jsonlite::fromJSON(args[[1]])
out <- args[[2]]
dir.create(out, recursive = TRUE, showWarnings = FALSE)
for (seed in config$seed_list) {
  set.seed(seed)
  values <- rexp(config$n, rate = 1)
  write.table(format(values, digits = 17, scientific = TRUE),
              file.path(out, paste0(seed, ".txt")),
              row.names = FALSE, col.names = FALSE, quote = FALSE)
}
