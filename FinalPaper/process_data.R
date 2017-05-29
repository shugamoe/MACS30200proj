# File to create variables and running models on r/changemyview data

library(tidyverse)
library(feather)
library(ineq)
library(anytime)
library(lubridate)
library(purrrlyr)

dat_cmv_auth_subs <- read_feather("~/MACS30200proj/changemyview/cmv_auth_subs.feather") %>%
  mutate(date = anytime(created_utc))
dat_cmv_subs <- read_feather("~/MACS30200proj/changemyview/cmv_subs.feather") %>%
  mutate(date = anytime(created_utc))

date_dif <- function(sub_date, prev_dates){
  lag_dates <- c(prev_dates[-1], sub_date) 
  (date_difs <- lag_dates - prev_dates)
}

STAND_IN <- dat_cmv_auth_subs[1, ]

model_indep_vars <- function(submission, num_prior_days, dat_cmv_auth_subs){
  if (num_prior_days == 0){
    time_filter <- 0
  } else {
    time_filter <- submission$created_utc - num_prior_days * 86400
  }
  force(dat_cmv_auth_subs)
  prior_subs <- dat_cmv_auth_subs %>%
    filter(author == submission$author,
           created_utc < submission$created_utc & 
             created_utc >= time_filter)
  num_prev <- nrow(prior_subs) 
  if (num_prev == 0){
    has_priors <- FALSE
  } else {
    has_priors <- TRUE
  }
  
  prev_cmv_subs <- sum(prior_subs$cmv_sub)
  if (nrow(prior_subs) != 0){
    last_sub <- tail(prior_subs, 1)
  } else {
    last_sub <- STAND_IN
  }
  
  subreddit_dist <- prior_subs %>%
    group_by(subreddit) %>%
    summarise(n = n())
  
  sub_time_delta <- date_dif(submission$date, prior_subs$date)
  prior_valid_subs <- prior_subs %>%
    filter(removed == FALSE & empty == FALSE)
  
  if (any(is.na(prior_valid_subs))){
    browser()
  }
  
  return_vec <- c(
                nrow(prior_subs),
                mean(prior_subs$score),
                ineq(subreddit_dist$n, type = "Gini"),
                has_priors,
                mean(prior_subs$removed),
                5,
                mean(prior_subs$empty),
                mean(prior_subs$sentiment),
                mean(sub_time_delta), 
                min(prior_subs$score),
                max(prior_subs$score),
                sd(prior_subs$score),
                min(prior_valid_subs$sentiment),
                sd(prior_valid_subs$sentiment),
                max(prior_valid_subs$sentiment),
                prev_cmv_subs,
                prev_cmv_subs / num_prev, # Fraction of subs that are CMV
                mean(prior_valid_subs$fps),
                mean(prior_valid_subs$fps_frac),
                mean(prior_valid_subs$fpp),
                mean(prior_valid_subs$fpp_frac),
                nrow(prior_valid_subs),
                last_sub$score,
                last_sub$empty,
                last_sub$fps,
                last_sub$fps_frac,
                last_sub$created_utc,
                last_sub$fpp,
                last_sub$fpp_frac,
                last_sub$cmv_sub,
                last_sub$removed,
                last_sub$sentiment,
                as.numeric(submission$created_utc - last_sub$created_utc),
                mean(prior_valid_subs$num_words)
                )
  (sub_info <- return_vec)
}

# This function creates the model data
# 
process_dat <- function(dat_cmv_subs, num_prior_days = 0, priors_only = TRUE){
  force(dat_cmv_subs)
  (model_dat <- dat_cmv_subs %>%
      by_row(model_indep_vars, dat_cmv_auth_subs = dat_cmv_auth_subs,
             num_prior_days = num_prior_days,
             .collate = "cols", .to = "indep_var") %>%
      rename(num_prior_subs = indep_var1,
             mean_sub_score = indep_var2,
             gini_index = indep_var3,
             has_priors = indep_var4,
             mean_rm_subs = indep_var5,
             mean_dl_subs = indep_var6,
             mean_empty_subs = indep_var7,
           mean_sub_sentiment = indep_var8,
           mean_daily_sub_freq = indep_var9,
           min_sub_score = indep_var10,
           max_sub_score =  indep_var11,
           sd_sub_score = indep_var12,
           min_sub_senti = indep_var13,
           sd_sub_senti = indep_var14,
           max_sub_senti = indep_var15,
           num_cmv_subs = indep_var16,
           frac_cmv_subs = indep_var17,
           mean_fps = indep_var18,
           mean_fps_frac = indep_var19,
           mean_fpp = indep_var20,
           mean_fpp_frac = indep_var21,
           num_valid_prior_subs = indep_var22,
           ls_score = indep_var23,
           ls_empty = indep_var24,
           ls_fps = indep_var25,
           ls_fps_frac = indep_var26,
           ls_created_utc = indep_var27,
           ls_fpp = indep_var28,
           ls_fpp_frac = indep_var29,
           ls_cmv_sub = indep_var30,
           ls_removed = indep_var31,
           ls_sentiment = indep_var32,
           time_since_ls = indep_var33,
           mean_num_words = indep_var34
           ) %>%
      mutate(mean_daily_sub_freq = mean_daily_sub_freq / 86400) %>%
      filter(has_priors == priors_only)
  )
}

processed_dat <- process_dat(dat_cmv_subs, num_prior_days = 0, priors_only = TRUE)
saveRDS(processed_dat, "~/MACS30200proj/FinalPaper/cmv_processed_dat.rds")
