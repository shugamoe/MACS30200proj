# Analyze the results of the trained models
#
#
library(ggplot2)
library(caret)
library(coefplot)

theme_set(theme_minimal())

# source("~/MACS30200proj/FinalPaper/train_model.R")

coef_names <- c(
         "(Post Debate) # Total Comments",
         "(Post Debate) # OP Comments" ,
         "(Post Debate) # Direct Comments" ,
         "(Pre Debate) # Words",
         "(Pre Debate) Singular First Person Pronouns" ,
         "(Pre Debate) Sentiment" ,
         "(Pre Debate) Plural First Person Pronouns" ,
         "(Pre Debate) Fraction Singular First Person Pronouns" ,
         "(Pre Debate) Fraction Plural First Person Pronouns",
         "(Pre Debate) Creation Time", 
         "(AH) Subreddit Gini Index" ,
         "(AH) # Submissions with Available Content",
         "(AH) # CMV Submissions" ,
         "(AH) Mean Submission Sentiment" ,
         "(AH) Mean Submission Score" ,
         "(AH) Mean Singular First Person Pronouns" ,
         "(AH) Mean Plural First Person Pronouns" ,
         "(AH) Mean # of Words",
         "(AH) Fraction Singular First Person Pronouns",
         "(AH) Fraction Removed Submissions" ,
         "(AH) Fraction Plural First Person Pronouns" ,
         "(AH) Fraction of CMV Submissions" ,
         "(AH) Fraction Empty Submissions" ,
         "(AH) Daily Submission Frequency" ,
         "(AH) Total Submission Score",
         "(AH) Total Singular First Person Pronouns",
         "(AH) Total Plural First Person Pronouns",
         "(AH) Total Removed Submissions",
         "(AH) # All Prior Submissions"
)

model_list <- readRDS("~/MACS30200proj/FinalPaper/results.rds")
new_model_names <- c("Standard (Pre Debate + AH)",
                     "Standard - Creation Time",
                     "# Words Only",
                     "Standard + Post Debate",
                     "Creation Time Only")

names(model_list) <- new_model_names

results <- resamples(model_list)

graph <- dotplot(results, # metric = c("ROC", "Sens", "Spec"),
                 scales = list(x = list(relation = "free",
                                        rot = 90
                 )),
                 main = "Model Evaluation Metrics")

coef_plot <- multiplot(model_list, intercept = FALSE, only = FALSE,
                       xlab = "Log Odds Value",
                       single = FALSE,
                       sort = "alphabetical",
                       # horizontal = TRUE,
                       # pointSize = 4,
                       scales = "fixed") + 
               # scale_y_discrete(labels = rev(coef_names)) +
               labs(title = "Coefficient Plot",
                    subtitle = "95% Confidence Level") + 
               ylab(label = "") +
               theme(legend.position = "none") + 
             theme(axis.text.y = element_text(size = 18),
                   legend.text = element_text(size = 18),
                   legend.title = element_text(size = 18),
                   strip.text.x = element_text(size = 14),
                   axis.title.x = element_text(size = 17),
                   axis.text.x  = element_text(size = 13, angle = 90)
                   ) +
              theme(plot.title = element_text(size = 20, hjust = 0.5),
                  plot.subtitle = element_text(hjust = 0.5))

     
graph
coef_plot

