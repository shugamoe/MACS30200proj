# Running logistic regression with 2016 changemyview submissions

library(caret)

ctrl <- trainControl(method = "repeatedcv", number = 10, savePredictions = TRUE)

mod_fit <- train(Class ~ Age + ForeignWorker + Property.RealEstate + Housing.Own + 
                   CreditHistory.Critical,  data = GermanCredit, method = "glm",
                 family = "binomial", trControl = ctrl, tuneLength = 5)

pred = predict(mod_fit, newdata = testing)
confusionMatrix(data = pred, testing$Class)