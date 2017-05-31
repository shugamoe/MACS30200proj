# Analyze the results of the trained models
#
#
library(ggplot2)
library(caret)
library(coefplot)

theme_set(theme_minimal())

# source("~/MACS30200proj/FinalPaper/train_model.R")

coef_names <- c(
         "(O) Creation Time", 
         "(O) Plural First Person Pronouns" ,
         "(O) Fraction Plural First Person Pronouns",
         "(O) Singular First Person Pronouns" ,
         "(O) Fraction Singular First Person Pronouns" ,
         "(O) # Words",
         "(O) Sentiment" ,
         "(O) Topic #",
         "(AH) # All Prior Submissions" ,
         "(AH) Mean Submission Score" ,
         "(AH) Subreddit Gini Index" ,
         "(AH) Fraction Removed Submissions" ,
         "(AH) Fraction Empty Submissions" ,
         "(AH) Mean Submission Sentiment" ,
         "(AH) Daily Submission Frequency" ,
         "(AH) # CMV Submissions" ,
         "(AH) Fraction of CMV Submissions" ,
         "(AH) Mean Singular First Person Pronouns" ,
         "(AH) Fraction Singular First Person Pronouns",
         "(AH) Mean Plural First Person Pronouns" ,
         "(AH) Fraction Plural First Person Pronouns" ,
         "(AH) # Submissions with Available Content",
         "(AH) Mean # of Words",
         "(AH) Total Submission Score",
         "(AH) Total Removed Submissions",
         "(AH) Total Singular First Person Pronouns",
         "(AH) Total Plural First Person Pronouns",
         "(Post Debate) # OP Comments" ,
         "(Post Debate) # Direct Comments" ,
         "(Post Debate) # Total Comments" 
)

model_list <- readRDS("~/MACS30200proj/FinalPaper/results.rds")
new_model_names <- c("Standard (O + AP)",
                     "Standard - Creation Time",
                     "# Words Only",
                     "Standard + Post Debate",
                     "Creation Time Only")

names(model_list) <- new_model_names

results <- resamples(model_list)

graph <- dotplot(results, metric = c("ROC", "Sens"), scales = list(x = list(relation = "free",
                                                 cex = c(1),
                                                 rot = 45),
                                        y = list(cex = c(2, 0))),
                 par.strip.text = list(cex = 2))

coef_plot <- multiplot(model_list, intercept = FALSE, only = FALSE,
                       sort = "alphabetical", single = FALSE, pointSize = 1.5,
                       xlab = "Log Odds Value",
                       dodgeHeight = 2) + 
             scale_y_discrete(labels = sort(coef_names)) + 
             labs(title = "",
                  legend = "") + 
             ylab(label = "") + 
             theme(axis.text.y = element_text(size = 18),
                   legend.text = element_text(size = 18),
                   legend.title = element_text(size = 18),
                   strip.text.x = element_text(size = 16.5),
                   axis.title.x = element_text(size = 17),
                   axis.text.x  = element_text(size = 14)) + 
             theme(panel.spacing = unit(1, "lines"),
                   legend.position = "none")
     
graph
coef_plot

