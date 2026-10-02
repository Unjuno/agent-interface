args <- commandArgs(trailingOnly = TRUE)
input_dir <- args[[1]]
output_path <- args[[2]]
fit_one <- function(x, u, method, siginit = NULL, shinit = NULL) {
  fit <- ismev::gpd.fit(x, threshold = u, show = FALSE, method = method,
                        siginit = siginit, shinit = shinit)
  list(method = method, start = c(siginit, shinit), convergence = fit$conv,
       mle = as.numeric(fit$mle), nll = as.numeric(fit$nllh))
}
seeds <- 65769931:65769936
rows <- lapply(seeds, function(seed) {
  sample_path <- file.path(input_dir, paste0(seed, ".txt"))
  x <- as.numeric(readLines(sample_path))
  u <- as.numeric(quantile(x, 0.90, type = 7))
  candidates <- order(x, decreasing = TRUE)[seq_len(2)]
  base <- x[-candidates]
  variants <- list(
    list(name = "default_nm", method = "Nelder-Mead", siginit = NULL, shinit = NULL),
    list(name = "nm_1_0", method = "Nelder-Mead", siginit = 1, shinit = 0),
    list(name = "nm_2_neg075", method = "Nelder-Mead", siginit = 2, shinit = -0.75),
    list(name = "nm_05_neg125", method = "Nelder-Mead", siginit = 0.5, shinit = -1.25),
    list(name = "default_bfgs", method = "BFGS", siginit = NULL, shinit = NULL),
    list(name = "bfgs_1_0", method = "BFGS", siginit = 1, shinit = 0)
  )
  fits <- lapply(variants, function(v) {
    result <- tryCatch(fit_one(base, u, v$method, v$siginit, v$shinit),
                       error = function(e) list(error = conditionMessage(e)))
    c(list(name = v$name), result)
  })
  list(seed = seed, n = length(x), threshold = u,
       sample_sha256 = strsplit(system2("sha256sum", sample_path,
                                        stdout = TRUE), " ")[[1]][[1]],
       candidate_indices = as.integer(candidates), fits = fits)
})
jsonlite::write_json(list(rows = rows), output_path, auto_unbox = TRUE,
                     digits = 17, pretty = FALSE, null = "null")
