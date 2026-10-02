args <- commandArgs(trailingOnly = TRUE)
input_path <- args[[1]]
output_path <- args[[2]]
source_dir <- args[[3]]
sample_dir <- args[[4]]
source(file.path(source_dir, "candidate_selection.R"))
source(file.path(source_dir, "shape_evaluation.R"))
source(file.path(source_dir, "CI_shapeGPD.R"))
source(file.path(source_dir, "TailID.R"))

cases <- jsonlite::fromJSON(input_path, simplifyVector = FALSE)
rows <- lapply(cases, function(case) {
  sample <- as.numeric(readLines(file.path(sample_dir, paste0(case$seed, ".txt"))))
  pm <- case$threshold_probability
  pc <- 1 - case$candidate_fraction_of_tail * (1 - pm)
  candidates <- candidate_selection(sample, pc, pc)
  threshold <- as.numeric(quantile(sample, pm, type = 7))
  candidate_indices <- as.integer(candidates[[1]])

  sample2 <- sample
  sample2[candidate_indices] <- NA_real_
  base_fit <- ismev::gpd.fit(na.omit(sample2), threshold = threshold, show = FALSE)
  base_ci <- CI_shapeGPD(sample2, threshold, base_fit$mle[[2]], case$confidence)

  state <- list(list(indices = candidate_indices, fit = base_fit$mle,
                     ci = base_ci, n_exceedances = base_fit$nexc,
                     convergence = base_fit$conv, nll = base_fit$nllh))
  upper_sensitive <- integer()
  ordered <- rev(candidate_indices)
  for (j in seq_along(ordered)) {
    index <- ordered[[j]]
    sample2[[index]] <- sample[[index]]
    fit <- ismev::gpd.fit(na.omit(sample2), threshold = threshold, show = FALSE)
    ci <- CI_shapeGPD(sample2, threshold, fit$mle[[2]], case$confidence)
    state[[length(state) + 1L]] <- list(indices = candidate_indices[seq_len(length(candidate_indices) - j)],
                                        restored_index = index, fit = fit$mle,
                                        ci = ci, n_exceedances = fit$nexc,
                                        convergence = fit$conv, nll = fit$nllh)
    if (!length(upper_sensitive) && fit$mle[[2]] > tail(state[[length(state) - 1L]]$ci, 1)) {
      upper_sensitive <- c(upper_sensitive, index)
    } else if (length(upper_sensitive)) {
      upper_sensitive <- c(upper_sensitive, index)
    }
  }
  tailid_indices <- as.integer(TailID(sample, pm, pm, pc, pc, case$confidence))
  list(case_id = case$case_id, seed = case$seed, n = length(sample),
       threshold = threshold, candidate_indices = candidate_indices,
       candidate_count_formula = (1 - pc) * length(sample),
       states = state, upper_sensitive_indices = sort(as.integer(upper_sensitive)),
       TailID_all_indices = tailid_indices,
       R_version = R.version.string,
       package_versions = list(ismev = as.character(packageVersion("ismev")),
                               jsonlite = as.character(packageVersion("jsonlite"))))
})
jsonlite::write_json(list(rows = rows), output_path, auto_unbox = TRUE,
                     digits = 17, pretty = FALSE, null = "null")
