args <- commandArgs(trailingOnly = TRUE)
input_dir <- args[[1]]
output_path <- args[[2]]
cfg <- jsonlite::fromJSON(args[[3]], simplifyVector = FALSE)
fit_one <- function(x, u, variant) {
  fit <- ismev::gpd.fit(x, threshold = u, show = FALSE,
                        method = variant$method,
                        siginit = variant$scale_start,
                        shinit = variant$shape_start)
  list(name = variant$name, method = variant$method,
       convergence = fit$conv, mle = as.numeric(fit$mle), nll = as.numeric(fit$nllh))
}
rows <- lapply(cfg$seeds, function(seed) {
  sample_path <- file.path(input_dir, paste0(seed, ".txt"))
  x <- as.numeric(readLines(sample_path))
  u <- as.numeric(quantile(x, cfg$threshold_probability, type = 7))
  candidates <- order(x, decreasing = TRUE)[seq_len(cfg$candidate_count)]
  base <- x[-candidates]
  fits <- lapply(cfg$r_fit_variants, function(v) {
    tryCatch(fit_one(base, u, v), error = function(e) list(name = v$name, error = conditionMessage(e)))
  })
  list(seed = seed, n = length(x), threshold = u,
       sample_sha256 = strsplit(system2("sha256sum", sample_path, stdout = TRUE), " ")[[1]][[1]],
       candidate_indices = as.integer(candidates), fits = fits)
})
jsonlite::write_json(list(rows = rows), output_path, auto_unbox = TRUE,
                     digits = 17, pretty = FALSE, null = "null")
