# Running logistic regression with 2016 changemyview submissions

library(caret)
library(purrr)
library(plyr)
library(tidyverse)
library(pROC)
library(doMC)

registerDoMC(2)
# Data preprocessing

CMV_DAT <- readRDS("MACS30200proj/FinalPaper/cmv_processed_dat.rds") %>%
  distinct(author, .keep_all = TRUE) %>%
  mutate(OP_gave_delta = factor(c(OP_gave_delta, recursive = TRUE), labels = c("stable", "changed"))) %>%
  dplyr::select(-c(author, num_deltas_from_OP, num_user_comments, href, date,
            has_priors, id, content, num_OP_comments, num_root_comments,
            title, mean_dl_subs)) %>% # No variation in deleted submissions
  dplyr::select(-starts_with("sd_"), -starts_with("max_"), -starts_with("min_")) %>%
  as.data.frame()

# for (i in 1:length(CMV_DAT)){
#   print(i)
#   CMV_DAT[[i]] <- as.data.frame(CMV_DAT[[i]] %>%
#     select(-c(author, num_deltas_from_OP, num_user_comments, href, date,
#               has_priors, id, content, num_OP_comments, num_root_comments,
#               title, sentiment))
#   )
# }

set.seed(69)
train_index <- createDataPartition(CMV_DAT$OP_gave_delta, p = .8, 
                                  list = FALSE, 
                                  times = 1)
CMV_DAT_TRAIN <- CMV_DAT[train_index, ]
CMV_DAT_TEST <- CMV_DAT[-train_index, ]

train_x <- CMV_DAT_TRAIN[names(CMV_DAT) != "OP_gave_delta"]
train_y <- CMV_DAT_TRAIN$OP_gave_delta


Grid <- expand.grid(list(ntree = seq(100, 1000, 100),
                         mtry = seq(2, 20, 2)))

ctrl <- trainControl(method = "LOOCV", number = 4, p = .8,
                     summaryFunction = twoClassSummary,
                     classProbs  = TRUE)

model <- train(train_x, train_y,
               method = "parRF",
               trControl = ctrl,
               preProc = c("center", "scale"),
               trace = 0,
               metric = "ROC",
               # tuneGrid = Grid,
               verbose = TRUE)


delta_accuracy <- CMV_DAT_TEST %>%
  add_predictions(model) %>%
  mutate(OP_gave_delta = ifelse(OP_gave_delta == "stable", 0, 1),
         pred = ifelse(pred == "stable", 0, 1))

auc_delta <- auc(delta_accuracy$OP_gave_delta, delta_accuracy$pred)

plot(roc(delta_accuracy$OP_gave_delta, delta_accuracy$pred), 
     main = sprintf("ROC Curve for Initial Logistic Model | AUC = %.3f", auc_delta))
