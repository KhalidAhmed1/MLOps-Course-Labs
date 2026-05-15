# Bank Customer Churn Prediction
# Bank Customer Churn Prediction (MLflow)

## Overview

This project implements an end-to-end machine learning pipeline for **bank customer churn prediction** with full **MLflow experiment tracking**. The pipeline covers data preprocessing, class rebalancing, feature engineering, model training, evaluation, and model logging.

Multiple models are trained and compared using MLflow to support proper model selection and lifecycle management (Staging vs Production).

---

## Problem Statement

Customer churn prediction aims to identify customers who are likely to leave the bank. This is a **binary classification problem** where:

* `Exited = 1` → Customer churned
* `Exited = 0` → Customer stayed

The business goal is to **maximize recall and F1-score**, since failing to detect a churned customer is more costly than a false alarm.

---

## Dataset

* **File**: `dataset/Churn_Modelling.csv`
* **Target Variable**: `Exited`
* **Features Used**:

  * CreditScore
  * Geography
  * Gender
  * Age
  * Tenure
  * Balance
  * NumOfProducts
  * HasCrCard
  * IsActiveMember
  * EstimatedSalary

---

## Project Structure

```
MLOps-Course-Labs/
│
├── src/
│   └── train.py
│
├── dataset/
│   └── Churn_Modelling.csv
│
└── README.md
```

---

## Data Preprocessing

The preprocessing pipeline includes:

1. **Class Rebalancing**

   * Downsampling the majority class using `sklearn.utils.resample`
   * Ensures balanced class distribution

2. **Train-Test Split**

   * 70% training
   * 30% testing

3. **Feature Transformation**

   * Numerical features scaled using `StandardScaler`
   * Categorical features encoded using `OneHotEncoder`
   * Implemented using `ColumnTransformer`

The trained preprocessor is logged to MLflow as an artifact.

---

## Models Implemented

The following models are supported and logged as separate MLflow experiments:

### 1. Logistic Regression (Baseline)

* Standard logistic regression
* Serves as a simple and interpretable baseline

### 2. Logistic Regression with L1 Regularization

* Uses L1 penalty for automatic feature selection
* Improves interpretability and reduces model complexity

### 3. Random Forest Classifier

* Ensemble-based model
* Captures non-linear feature interactions
* Typically improves F1-score and recall

### 4. Gradient Boosting Classifier

* Strong performer on tabular data
* Optimized using:

  * `n_estimators = 150`
  * `learning_rate = 0.05`
  * `max_depth = 3`

---

## Experiment Tracking with MLflow

Each training run logs the following to MLflow:

### Parameters

* Model type
* Hyperparameters (e.g., max_depth, n_estimators, penalty)

### Metrics

* Accuracy
* Precision
* Recall
* F1-score

### Artifacts

* Trained model
* Preprocessing pipeline
* Confusion matrix plot
* Training dataset metadata


## Running the Experiment

### 1. Start MLflow Tracking Server

```bash
mlflow ui
```

Or ensure the server is running at:

```
http://localhost:5000
```

### 2. Run Training Script

From the project root directory:

```bash
python src/train.py
```

Each execution creates a **new MLflow run**.

---

## Model Selection and Registry

Using MLflow UI:

1. Compare experiments based on F1-score and recall
2. Register selected models under a common name
3. Assign stages:

   * **Production**: Best-performing model (highest F1 and recall)
   * **Staging**: Stable or interpretable model for validation

### Justification Example

* **Production Model**: Gradient Boosting

  * Highest F1-score and recall
  * Best trade-off for churn detection

* **Staging Model**: Random Forest Classifier

  * High interpretability
  * Suitable for business review and monitoring

---

## Key Takeaways

* Multiple experiments are tracked reproducibly
* MLflow enables transparent comparison and governance
* The pipeline follows MLOps best practices
* Suitable for real-world deployment scenarios



