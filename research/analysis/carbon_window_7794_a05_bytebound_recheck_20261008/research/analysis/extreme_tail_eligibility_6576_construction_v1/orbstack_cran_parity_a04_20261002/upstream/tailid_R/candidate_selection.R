#' Selects the candidates of the tail
#'
#' This function selects the candidates of the tail that can be inconsistent to the ID hypothesis
#'
#' @param sample A numeric vector.
#' @param pc_max A number between pm_max and 1  indicating the threshold of maximum sensitive points to consider.
#' @param pc_min A number between pm_min and 1  indicating the threshold of minimum sensitive points to consider.
#'
#' @return A vector of indices corresponding to the detected sensitive points.
#' @examples
#' candidate_selection(rnorm(1000), 0.99, 0.99)
#' candidate_selection(c(rnorm(10^3,10,1),rnorm(10,20,3)), 0.9, 0.9)
#' @export

candidate_selection <- function(sample, pc_max, pc_min) {
  indices_sample <- data.frame(
    original_index = integer(length(sample)),
    value = numeric(length(sample))
  )
  for (c in 1:length(sample)) {
    indices_sample$original_index[c] <- c
    indices_sample$value[c] <- sample[c]
  }
  #Select the maximum candidates
  num_senstives_max <- (1 - pc_max) * length(sample)
  sensible_candidates2_max <- indices_sample$original_index[order(- (indices_sample$value - mean(sample)))][1:num_senstives_max]
  sensible_candidates_max <- sensible_candidates2_max[order(sensible_candidates2_max)]

  #Select the minimum candidates
  num_senstives_min <- (1 - pc_min) * length(sample)
  sensible_candidates2_min <- indices_sample$original_index[order((indices_sample$value - mean(sample)))][1:num_senstives_min]
  sensible_candidates_min <- sensible_candidates2_min[order(sensible_candidates2_min)]
  return(list(sensible_candidates2_max, sensible_candidates2_min))
}

