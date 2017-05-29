# Running logistic regression with 2016 changemyview submissions

library(caret)
library(purrr)
library(plyr)
library(tidyverse)
library(pROC)
library(doMC)
library(modelr)
library(stringr)
library(tidytext)
library(perm)

registerDoMC(2)
theme_set(theme_minimal())

# Data preprocessing

CMV_DAT <- readRDS("MACS30200proj/FinalPaper/cmv_processed_dat.rds") %>%
  distinct(author, .keep_all = TRUE) %>% # One author only
  filter(!str_detect(title, "Fresh Topic Friday")) %>% # Take out meta posts
  # filter(num_OP_comments >= 1 & num_user_comments >= 10) %>% # Filtering procedure of Tan et al.
  mutate(OP_gave_delta = factor(OP_gave_delta, labels = c("stable", "changed")),
         created_utc = as.numeric(created_utc)) %>%
  dplyr::select(-c(author, num_deltas_from_OP, num_user_comments, href, date,
            has_priors, id, content, num_OP_comments, num_root_comments,
            title, mean_dl_subs)) %>% # No variation in deleted submissions
  # Last Submission statistics removal
  dplyr::select(-c(ls_score, ls_fps, ls_created_utc, ls_fpp_frac, ls_removed, time_since_ls,
                   ls_fps_frac, ls_cmv_sub, ls_fpp, ls_sentiment, ls_empty, ls_fpp)) %>%
  # dplyr::select(-c(created_utc, ls_created_utc)) %>% # time removal
  dplyr::select(-starts_with("sd_"), -starts_with("max_"), -starts_with("min_")) %>%
  drop_na() %>%
  mutate(created_utc = created_utc / 86400) %>%
  as.data.frame()
# for (i in 1:length(CMV_DAT)){
#   print(i)
#   CMV_DAT[[i]] <- as.data.frame(CMV_DAT[[i]] %>%
#     select(-c(author, num_deltas_from_OP, num_user_comments, href, date,
#               has_priors, id, content, num_OP_comments, num_root_comments,
#               title, sentiment))
#   )
# }


CMV_DAT_POST <- readRDS("MACS30200proj/FinalPaper/cmv_processed_dat.rds") %>%
  distinct(author, .keep_all = TRUE) %>% # One author only
  filter(!str_detect(title, "Fresh Topic Friday")) %>% # Take out meta posts
  # filter(num_OP_comments >= 1 & num_user_comments >= 10) %>% # Filtering procedure of Tan et al.
  mutate(OP_gave_delta = factor(OP_gave_delta, labels = c("stable", "changed")),
         created_utc = as.numeric(created_utc)) %>%
  dplyr::select(-c(author, num_deltas_from_OP, href, date,
            has_priors, id, content,
            title, mean_dl_subs)) %>% # No variation in deleted submissions
  # Last Submission statistics removal
  dplyr::select(-c(ls_score, ls_fps, ls_created_utc, ls_fpp_frac, ls_removed, time_since_ls,
                   ls_fps_frac, ls_cmv_sub, ls_fpp, ls_sentiment, ls_empty, ls_fpp)) %>%
  # dplyr::select(-c(created_utc, ls_created_utc)) %>% # time removal
  dplyr::select(-starts_with("sd_"), -starts_with("max_"), -starts_with("min_")) %>%
  drop_na() %>%
  mutate(created_utc = created_utc / 86400) %>%
  as.data.frame()


set.seed(69)
train_index <- createDataPartition(CMV_DAT$OP_gave_delta, p = .8,
                                  list = FALSE,
                                  times = 1)
CMV_DAT_TRAIN <- CMV_DAT[train_index, ]
CMV_DAT_TEST <- CMV_DAT[-train_index, ]

POST_TRAIN <- CMV_DAT_POST[train_index, ]
POST_TEST <- CMV_DAT_POST[-train_index, ]

train_x <- CMV_DAT_TRAIN[names(CMV_DAT) != "OP_gave_delta"]
train_y <- CMV_DAT_TRAIN$OP_gave_delta


Grid1 <- expand.grid(list(nIter = seq(50, 300, 10)))

ctrl1 <- trainControl(method = "repeatedcv", number = 5, repeats = 5,
                     summaryFunction = twoClassSummary,
                     classProbs  = TRUE, search = "random")


model1 <- train(OP_gave_delta ~ .,
               data = CMV_DAT_TRAIN,
               method = "LogitBoost",
               trControl = ctrl1,
               tuneGrid = Grid1,
               metric = "ROC")

ctrl2 <- trainControl(method = "repeatedcv", number = 5, repeats = 5,
                     summaryFunction = twoClassSummary,
                     classProbs  = TRUE, search = "random")

model2 <- train(OP_gave_delta ~ . + num_prior_subs:mean_sub_score + 
                  num_prior_subs:mean_rm_subs,
                data = CMV_DAT_TRAIN,
                method = "glm",
                metric = "ROC",
                trControl = ctrl2)

model2base <- train(OP_gave_delta ~ 1 + num_words,
                 data = CMV_DAT_TRAIN,
                 method = "glm",
                 metric = "ROC",
                 trControl = ctrl2)


# Grid3 <- expand.grid(mtry = seq(10, 300, 10))
# ctrl3 <- trainControl(method = "repeatedcv", number = 5, repeats = 5,
#                       summaryFunction = twoClassSummary,
#                       classProbs = TRUE, search = "random")
# 
# model3 <- train(train_x, train_y,
#                 method = "rf",
#                 metric = "ROC",
#                 tuneGrid = Grid3, 
#                 trControl = ctrl3)

Grid4 <- expand.grid(list(cp = "aic", lambda = seq(.0001, .1, .001)))

model_auc <- function(model, test_dat = CMV_DAT_TEST){
  dat_with_preds <- test_dat %>%
    add_predictions(model) %>%
    mutate(OP_gave_delta = ifelse(OP_gave_delta == "stable", 0, 1),
           pred = ifelse(pred == "stable", 0, 1))
  
  list(dat = dat_with_preds, auc = auc(dat_with_preds$OP_gave_delta,
                                       dat_with_preds$pred))
}

graph_roc <- function(model, test_dat = CMV_DAT_TEST){
  graph_dat <- model_auc(model, test_dat)  
  plot(roc(graph_dat[["dat"]]$OP_gave_delta, graph_dat[["dat"]]$pred),
           xlim = c(1, 0),
           main = sprintf("%s | AUC = %.3f", model$method,
                         graph_dat[["auc"]]))
}


model_post <- train(OP_gave_delta ~ . + num_prior_subs:mean_sub_score + 
                  num_prior_subs:mean_rm_subs,
                data = POST_TRAIN,
                method = "glm",
                metric = "ROC",
                trControl = ctrl2)

# glm_dat <- auc_conf_int("glm")
# blr_dat <- auc_conf_int("LogitBoost")

# graph_roc(model1)
results_dat <- list(
  model2 = model2,
  model2base = model2base,
  model_post = model_post,
  model2_dat = model_auc(model2),
  model2base_dat = model_auc(model2base),
  model_post_dat = model_auc(model_post, POST_TEST)
)

saveRDS(results_dat, "~/MACS30200proj/FinalPaper/results.rds")

graph_roc(model2)
graph_roc(model2base)
graph_roc(model_post, POST_TEST)
# graph_roc(model3)






# delta_accuracy <- CMV_DAT_TEST %>%
#   add_predictions(model) %>%
#   mutate(OP_gave_delta = ifelse(OP_gave_delta == "stable", 0, 1),
#          pred = ifelse(pred == "stable", 0, 1))
# 
# auc_delta <- auc(delta_accuracy$OP_gave_delta, delta_accuracy$pred)
# 
# plot(roc(delta_accuracy$OP_gave_delta, delta_accuracy$pred), xlim = c(1, 0),
#      main = sprintf("ROC Curve for Initial Logistic Model | AUC = %.3f", auc_delta))

auc_conf_int <- function(method, ints = 1:100){
  models_n_auc <- list(models = list(),
                       auc = c())
  for (num in ints){
    set.seed(69)
    iter_train_index <- createDataPartition(CMV_DAT$OP_gave_delta, p = .8, 
                                      list = FALSE, 
                                      times = 1)
    iter_train <- CMV_DAT[iter_train_index, ]
    iter_test <- CMV_DAT[-iter_train_index, ]
    
    iter_ctrl <- trainControl(method = "repeatedcv", number = 5, repeats = 5,
                         summaryFunction = twoClassSummary,
                         classProbs  = TRUE, search = "random")
    
    if (method == "LogitBoost"){
      iter_grid <- expand.grid(list(nIter = seq(50, 300, 10)))
      
      
      iter_model <- train(OP_gave_delta ~ .,
                     data = iter_train,
                     method = "LogitBoost",
                     trControl = iter_ctrl,
                     tuneGrid = iter_grid,
                     metric = "ROC")
    } else if (method == "glm"){
      iter_model <- train(OP_gave_delta ~ .,
                          data = iter_train, 
                          method = "glm",
                          trControl = iter_ctrl,
                          metric = "ROC")   
    }
      iter_test <- iter_test %>%
        add_predictions(iter_model) %>%
        mutate(OP_gave_delta = ifelse(OP_gave_delta == "stable", 0, 1),
               pred = ifelse(pred == "stable", 0, 1))
      models_n_auc[["auc"]] <- append(models_n_auc[["auc"]], 
                                      auc(iter_test$OP_gave_delta, iter_test$pred))
      models_n_auc[["models"]] <- append(models_n_auc[["models"]],
                                         iter_model)
  }
  models_n_auc
}