#' Evaluation of the shape parameter to return inconsistent points and shape parameters computed and its confidence intervals
#'
#' This function detects the points of the tail that are inconsistent with the ID hypothesis by evaluation the shape variation of the GPD,
#' and also returns the shape parameters computed and its confidence intervals
#'
#' @param sample A numeric vector.
#' @param candidates A list of indices of the sample.
#' @param pm_max A number between 0 and 1 indicating the threshold of maximum extreme values to consider.
#' @param pm_min A number between 0 and 1 indicating the threshold of maximum extreme values to consider.
#' @param conf_level A number between 0 and 1 indicating the confidence level for the detection.
#'
#' @return A vector of indices corresponding to the detected sensitive points.
#' @examples
#' shape_evaluation(rnorm(1000),candidate_selection(rnorm(1000), 0.99, 0.99),
#'  0.8, 0.8, 0.95)
#' shape_evaluation(c(rnorm(10^3,10,1),rnorm(10,20,3)),
#' candidate_selection(c(rnorm(10^3,10,1),rnorm(10,20,3)), 0.9, 0.9),
#' 0.8, 0.8, 0.9999)
#' @importFrom stats na.omit quantile
#' @export

shape_evaluation <- function(sample, candidates, pm_max, pm_min, conf_level) {
  sensitive_max <- list()
  sensitive_min <- list()

  sensitive_candidates2_max <- candidates[[1]]
  sensitive_candidates2_min <- candidates[[2]]

  #Select excess set
  threshold_max <- quantile(na.omit(sample), pm_max)[[1]]
  threshold_min <- quantile(na.omit(-sample), pm_min)[[1]]

  #Remove candidates from the sample
  sample2 <- sample
  sample2[sensitive_candidates2_max] <- NA
  sample2[sensitive_candidates2_min] <- NA

  #Fit GPD shape
  shape_max <- list()
  shape_min <- list()
  parameter_max <- ismev::gpd.fit(na.omit(sample2), threshold = threshold_max)$mle[2]
  parameter_min <- ismev::gpd.fit(na.omit(-sample2), threshold = threshold_min)$mle[2]
  shape_max <- c(shape_max, parameter_max)
  shape_min <- c(shape_min, parameter_min)

  #Compute confidence interval
  int_conf_max <- CI_shapeGPD(sample2, threshold_max, parameter_max, conf_level)
  int_conf_min <- CI_shapeGPD(-sample2, threshold_min, parameter_min, conf_level)

  #Iterative Candidate Evaluation Step for Maximum Values
  for(t in (0:(length(sensitive_candidates2_max) - 1))){
    #Add candidate back to the dataset
    sample2[sensitive_candidates2_max[length(sensitive_candidates2_max)-t]] <- sample[sensitive_candidates2_max[length(sensitive_candidates2_max)-t]]

    #Fit GPD shape
    shape_max <- append(shape_max,ismev::gpd.fit(na.omit(sample2), threshold = threshold_max)$mle[2])

    if(length(sensitive_max) ==0){
      if(ismev::gpd.fit(na.omit(sample2), threshold = threshold_max)$mle[2]  > int_conf_max[length(int_conf_max)]){
        #Add point to the list if it is inconsistent
        sensitive_max <- rbind(sensitive_max, sensitive_candidates2_max[length(sensitive_candidates2_max)-t])
        int_conf_max <- c(int_conf_max, c(NA,NA))
      }else{
        #Update confidence interval
        int_conf_max <- c(int_conf_max, CI_shapeGPD(sample2, threshold_max, unlist(shape_max[length(shape_max)]), conf_level))
      }
    }else{
      #Add point to the list if not empty
      int_conf_max <- c(int_conf_max, c(NA,NA))
      sensitive_max <- rbind(sensitive_max, sensitive_candidates2_max[length(sensitive_candidates2_max)-t])
    }
  }

  #Iterative Candidate Evaluation Step for Minimum Values
  for(t in (0:(length(sensitive_candidates2_min) - 1))){
    #Add candidate back to the dataset
    sample2[sensitive_candidates2_min[length(sensitive_candidates2_min)-t]] <- sample[sensitive_candidates2_min[length(sensitive_candidates2_min)-t]]

    #Fit GPD shape
    shape_min <- append(shape_min,ismev::gpd.fit(na.omit(-sample2), threshold = threshold_min)$mle[2])
    if(length(sensitive_min) ==0){
      if(ismev::gpd.fit(na.omit(-sample2), threshold = threshold_min)$mle[2]  > int_conf_min[length(int_conf_min)]){
        #Add point to the list if it is inconsistent
        sensitive_min <- rbind(sensitive_min, sensitive_candidates2_min[length(sensitive_candidates2_min)-t])
        int_conf_min <- c(int_conf_min, c(NA,NA))
      }else{
        #Update confidence interval
        int_conf_min <- c(int_conf_min, CI_shapeGPD(-sample2, threshold_min, unlist(shape_min[length(shape_min)]), conf_level))
      }
    }else{
      #Add point to the list if not empty
      int_conf_min <- c(int_conf_min, c(NA,NA))
      sensitive_min <- rbind(sensitive_min, sensitive_candidates2_min[length(sensitive_candidates2_min)-t])
    }
  }

  #Return inconsitent points
  sensitive_max <- unlist(sensitive_max)
  sensitive_min <- unlist(sensitive_min)
  sensitive_points <- unlist(c(sensitive_min, sensitive_max))

  return(list(shape_max, shape_min, int_conf_max, int_conf_min, sensitive_points))
}


