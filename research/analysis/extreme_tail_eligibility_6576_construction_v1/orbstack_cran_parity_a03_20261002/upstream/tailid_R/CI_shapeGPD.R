#' Computes a Confidence Interval for a GPD shape
#'
#' This function computes a confidence interval for a GPD shape.
#'
#' @param sample A numeric vector.
#' @param threshold A number between 0 and 1 indicating the threshold of extreme values to consider.
#' @param parameter A number  indicating the shape value.
#' @param conf_level A number between 0 and 1 indicating the confidence level for the detection.
#'
#' @return A Confidence Interval vector.
#' @examples
#' CI_shapeGPD(rnorm(1000), 0.8, 1, 0.95)
#' CI_shapeGPD(c(rnorm(10^3,10,1),rnorm(10,20,3)), 0.8, 12, 0.9999)
#' @importFrom stats na.omit qnorm
#' @export

CI_shapeGPD <- function(sample, threshold, parameter, conf_level) {
  #Compute the length of the sample and
  n <- length(na.omit(sample)[na.omit(sample) > threshold])
  alpha <- 1 - conf_level

  #Compute the bounds
  ci_lower <- qnorm(alpha / 2, mean = 0, sd = abs(parameter))
  ci_upper <- qnorm(1 - alpha / 2, mean = 0, sd = abs(parameter))
  ci_lower <- ci_lower/(sqrt(n))
  ci_upper <- ci_upper/sqrt(n)
  ci_lower <- parameter + ci_lower
  ci_upper <- parameter + ci_upper
  vector <- c(ci_lower, ci_upper)
  return(c(min(vector), max(vector)))
}
