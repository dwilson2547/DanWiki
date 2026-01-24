# Machine Learning Fundamental Concepts

An introduction to core machine learning concepts and terminology.

## What is Machine Learning?

Machine Learning (ML) is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. ML algorithms build mathematical models based on sample data to make predictions or decisions.

## Types of Machine Learning

### Supervised Learning

The algorithm learns from labeled training data. Each example includes input features and the correct output.

**Common algorithms:**
- Linear Regression
- Logistic Regression
- Decision Trees
- Random Forests
- Support Vector Machines (SVM)
- Neural Networks

**Use cases:**
- Spam detection
- Image classification
- Price prediction
- Medical diagnosis

### Unsupervised Learning

The algorithm finds patterns in unlabeled data without predetermined categories.

**Common algorithms:**
- K-Means Clustering
- Hierarchical Clustering
- Principal Component Analysis (PCA)
- Autoencoders

**Use cases:**
- Customer segmentation
- Anomaly detection
- Dimensionality reduction
- Recommendation systems

### Reinforcement Learning

Agent learns by interacting with environment and receiving rewards or penalties.

**Components:**
- Agent: Learner or decision maker
- Environment: What the agent interacts with
- Actions: What the agent can do
- Rewards: Feedback signal

**Use cases:**
- Game playing (Chess, Go)
- Robotics
- Autonomous vehicles
- Resource optimization

## Key Concepts

### Features and Labels

- **Features**: Input variables (X) used to make predictions
- **Labels**: Output variable (y) we want to predict
- **Feature Engineering**: Creating new features from raw data

### Training and Testing

Split data into:
- **Training set**: Used to train the model (typically 70-80%)
- **Validation set**: Used to tune hyperparameters (10-15%)
- **Test set**: Final evaluation (10-15%)

### Overfitting and Underfitting

- **Overfitting**: Model learns training data too well, including noise
  - High training accuracy, low test accuracy
  - Solution: Regularization, more data, simpler model
  
- **Underfitting**: Model too simple to capture patterns
  - Low training and test accuracy
  - Solution: More complex model, better features

### Bias and Variance

- **Bias**: Error from incorrect assumptions
  - High bias → underfitting
  
- **Variance**: Error from sensitivity to training data fluctuations
  - High variance → overfitting

**Bias-Variance Tradeoff**: Balance between bias and variance for optimal performance

### Loss Functions

Measure how well model predictions match actual values:

- **Mean Squared Error (MSE)**: For regression
  ```
  MSE = (1/n) Σ(y_actual - y_predicted)²
  ```

- **Cross-Entropy Loss**: For classification
  ```
  Loss = -Σ y_actual * log(y_predicted)
  ```

### Gradient Descent

Optimization algorithm to minimize loss function:

1. Initialize parameters randomly
2. Calculate gradient of loss function
3. Update parameters in direction of steepest descent
4. Repeat until convergence

**Variants:**
- Batch Gradient Descent
- Stochastic Gradient Descent (SGD)
- Mini-batch Gradient Descent
- Adam, RMSprop (adaptive methods)

## Model Evaluation Metrics

### Classification

- **Accuracy**: (TP + TN) / Total
- **Precision**: TP / (TP + FP)
- **Recall**: TP / (TP + FN)
- **F1 Score**: Harmonic mean of precision and recall
- **ROC-AUC**: Area under ROC curve

### Regression

- **Mean Absolute Error (MAE)**
- **Mean Squared Error (MSE)**
- **Root Mean Squared Error (RMSE)**
- **R² Score**: Proportion of variance explained

## Common Challenges

1. **Insufficient Training Data**: Need representative samples
2. **Poor Data Quality**: Garbage in, garbage out
3. **Irrelevant Features**: Feature selection is crucial
4. **Unrepresentative Training Data**: Sampling bias
5. **Imbalanced Classes**: One class dominates the dataset

## Best Practices

1. Start simple, then increase complexity
2. Always split your data properly
3. Use cross-validation for robust evaluation
4. Monitor both training and validation metrics
5. Perform feature scaling/normalization
6. Handle missing data appropriately
7. Try ensemble methods for better performance
8. Document experiments and results

## Next Steps

- Learn about deep learning and neural networks
- Explore specific algorithms in detail
- Practice with real-world datasets (Kaggle, UCI ML Repository)
- Study advanced topics: Transfer Learning, GANs, Transformers
