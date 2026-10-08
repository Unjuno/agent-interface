#' Detects the sensitive points in the Tail
#'
#' This function returns the points of the tail that are inconsistent with the ID hypothesis.
#'
#' @param sample A numeric vector.
#' @param pm_max A number between 0 and 1 indicating the threshold of maximum extreme values to consider.
#' @param pm_min A number between 0 and 1 indicating the threshold of minimum extreme values to consider.
#' @param pc_max A number between pm_max and 1  indicating the threshold of maximum sensitive points to consider.
#' @param pc_min A number between pm_min and 1 indicating the threshold of minimum sensitive points to consider.
#' @param conf_level A number between 0 and 1 indicating the confidence level for the detection.
#'
#' @return A vector of indices corresponding to the detected sensitive points.
#' @examples
#' TailID(rnorm(1000), 0.8, 0.8, 0.99, 0.99, 0.95)
#' TailID(c(rnorm(10^3,10,1),rnorm(10,20,3)), 0.8, 0.8, 0.9, 0.9, 0.9999)
#' @export

TailID <- function(sample, pm_max, pm_min, pc_max, pc_min, conf_level) {

  #Select the candidates
  candidates <- candidate_selection(sample, pc_max, pc_min)

  #Detect the inconsistent points
  sensitive_points <- shape_evaluation(sample, candidates, pm_max, pm_min, conf_level)[[5]]
  return(sensitive_points)
}

