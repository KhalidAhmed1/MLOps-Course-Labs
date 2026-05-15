"""
This module contains functions to preprocess and train the model
for bank consumer churn prediction.
"""

import pandas as pd
import matplotlib.pyplot as plt
from sklearn.utils import resample
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.compose import make_column_transformer
from sklearn.preprocessing import OneHotEncoder,  StandardScaler
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    ConfusionMatrixDisplay,
)
from sklearn.ensemble import RandomForestClassifier

### Import MLflow
import mlflow

def rebalance(data):
    """
    Resample data to keep balance between target classes.

    The function uses the resample function to downsample the majority class to match the minority class.

    Args:
        data (pd.DataFrame): DataFrame

    Returns:
        pd.DataFrame): balanced DataFrame
    """
    churn_0 = data[data["Exited"] == 0]
    churn_1 = data[data["Exited"] == 1]
    if len(churn_0) > len(churn_1):
        churn_maj = churn_0
        churn_min = churn_1
    else:
        churn_maj = churn_1
        churn_min = churn_0
    churn_maj_downsample = resample(
        churn_maj, n_samples=len(churn_min), replace=False, random_state=1234
    )

    return pd.concat([churn_maj_downsample, churn_min])


def preprocess(df):
    """
    Preprocess and split data into training and test sets.

    Args:
        df (pd.DataFrame): DataFrame with features and target variables

    Returns:
        ColumnTransformer: ColumnTransformer with scalers and encoders
        pd.DataFrame: training set with transformed features
        pd.DataFrame: test set with transformed features
        pd.Series: training set target
        pd.Series: test set target
    """
    filter_feat = [
        "CreditScore",
        "Geography",
        "Gender",
        "Age",
        "Tenure",
        "Balance",
        "NumOfProducts",
        "HasCrCard",
        "IsActiveMember",
        "EstimatedSalary",
        "Exited",
    ]
    cat_cols = ["Geography", "Gender"]
    num_cols = [
        "CreditScore",
        "Age",
        "Tenure",
        "Balance",
        "NumOfProducts",
        "HasCrCard",
        "IsActiveMember",
        "EstimatedSalary",
    ]
    data = df.loc[:, filter_feat]
    data_bal = rebalance(data=data)
    X = data_bal.drop("Exited", axis=1)
    y = data_bal["Exited"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=1912
    )
    col_transf = make_column_transformer(
        (StandardScaler(), num_cols), 
        (OneHotEncoder(handle_unknown="ignore", drop="first"), cat_cols),
        remainder="passthrough",
    )

    X_train = col_transf.fit_transform(X_train)
    X_train = pd.DataFrame(X_train, columns=col_transf.get_feature_names_out())

    X_test = col_transf.transform(X_test)
    X_test = pd.DataFrame(X_test, columns=col_transf.get_feature_names_out())

    # Log the transformer as an artifact
    mlflow.sklearn.log_model(col_transf, artifact_path="preprocessor")
    
    return col_transf, X_train, X_test, y_train, y_test


def train(X_train, y_train):
    """
    Train a logistic regression model.

    Args:
        X_train (pd.DataFrame): DataFrame with features
        y_train (pd.Series): Series with target

    Returns:
        LogisticRegression: trained logistic regression model
    """
    log_reg = LogisticRegression(max_iter=1000)
    log_reg.fit(X_train, y_train)

    ### Log the model with the input and output schema
    # Infer signature (input and output schema)
    signature = mlflow.models.infer_signature(X_train, log_reg.predict(X_train))  
    
    # Log model
    mlflow.sklearn.log_model(log_reg, "model", signature=signature)

    ### Log the data
    dataset = mlflow.data.from_pandas(X_train, source="dataset/Churn_Modelling.csv", name="training_data")
    mlflow.log_input(dataset, context="training")

    return log_reg


def train_logistic_l1(X_train, y_train):
    model = LogisticRegression(
        penalty="l1",
        solver="liblinear",
        max_iter=1000
    )
    model.fit(X_train, y_train)

    mlflow.log_param("model_type", "LogisticRegression")
    mlflow.log_param("penalty", "l1")
    mlflow.log_param("solver", "liblinear")

    signature = mlflow.models.infer_signature(
        X_train, model.predict(X_train)
    )

    mlflow.sklearn.log_model(model, "model", signature=signature)

    dataset = mlflow.data.from_pandas(X_train, source="dataset/Churn_Modelling.csv", name="training_data")
    mlflow.log_input(dataset, context="training")
    return model


def train_random_forest(X_train, y_train):
    rf = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        random_state=42
    )
    rf.fit(X_train, y_train)

    mlflow.log_param("model_type", "RandomForest")
    mlflow.log_param("n_estimators", 200)
    mlflow.log_param("max_depth", 10)

    signature = mlflow.models.infer_signature(
        X_train, rf.predict(X_train)
    )

    mlflow.sklearn.log_model(
        rf,
        artifact_path="model",
        signature=signature
    )
    dataset = mlflow.data.from_pandas(X_train, source="dataset/Churn_Modelling.csv", name="training_data")
    mlflow.log_input(dataset, context="training")

    return rf

from sklearn.ensemble import GradientBoostingClassifier
def train_gradient_boosting(X_train, y_train):
    gb = GradientBoostingClassifier(
        n_estimators=150,
        learning_rate=0.05,
        max_depth=3,
        random_state=42
    )
    gb.fit(X_train, y_train)

    mlflow.log_param("model_type", "GradientBoosting")
    mlflow.log_param("n_estimators", 150)
    mlflow.log_param("learning_rate", 0.05)

    signature = mlflow.models.infer_signature(
        X_train, gb.predict(X_train)
    )

    mlflow.sklearn.log_model(gb, "model", signature=signature)
    dataset = mlflow.data.from_pandas(X_train, source="dataset/Churn_Modelling.csv", name="training_data")
    mlflow.log_input(dataset, context="training")
    return gb




def main():
    ### Set the tracking URI for MLflow
    mlflow.set_tracking_uri("http://localhost:5000") 


    ### Set the experiment name
    mlflow.set_experiment("Bank_Churn_Prediction")


    ### Start a new run and leave all the main function code as part of the experiment
    with mlflow.start_run():

        df = pd.read_csv("dataset/Churn_Modelling.csv")
        col_transf, X_train, X_test, y_train, y_test = preprocess(df)

        ### Log the max_iter parameter
        mlflow.log_param("max_iter", 1000)


        # model = train(X_train, y_train)
        # model = train_random_forest(X_train, y_train)
        # model = train_logistic_l1(X_train, y_train)
        model = train_gradient_boosting(X_train, y_train)

        y_pred = model.predict(X_test)

        ### Log metrics after calculating them
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)

        mlflow.log_metric("accuracy", accuracy)
        mlflow.log_metric("precision", precision)
        mlflow.log_metric("recall", recall)
        mlflow.log_metric("f1_score", f1)

        ### Log tag
        mlflow.set_tag("version", "1.0.0")

        conf_mat = confusion_matrix(y_test, y_pred, labels=model.classes_)
        conf_mat_disp = ConfusionMatrixDisplay(
            confusion_matrix=conf_mat, display_labels=model.classes_
        )
        conf_mat_disp.plot()
        
        # Log the image as an artifact in MLflow
        plt.savefig("confusion_matrix.png")
        mlflow.log_artifact("confusion_matrix.png")
        plt.show()


if __name__ == "__main__":
    main()
