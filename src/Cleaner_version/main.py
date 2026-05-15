import pandas as pd
import matplotlib.pyplot as plt
import mlflow
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, ConfusionMatrixDisplay
from data_utils import preprocess_data
from models import log_and_train

def run_experiment(model_key="gb"):
    data_path = "dataset/Churn_Modelling.csv"
    
    mlflow.set_tracking_uri("http://localhost:5000")
    mlflow.set_experiment("Bank_Churn_Prediction")

    with mlflow.start_run():
        # Load and Preprocess
        df = pd.read_csv(data_path)
        transformer, X_train, X_test, y_train, y_test = preprocess_data(df)
        mlflow.sklearn.log_model(transformer, "preprocessor")

        # Select Model Configuration
        configs = {
            "lr": (LogisticRegression(), {"max_iter": 1000, "penalty": "l1", "solver": "liblinear"}),
            "rf": (RandomForestClassifier(), {"n_estimators": 200, "max_depth": 10, "random_state": 42}),
            "gb": (GradientBoostingClassifier(), {"n_estimators": 150, "learning_rate": 0.05, "max_depth": 3})
        }
        
        base_model, params = configs[model_key]
        model = log_and_train(base_model, X_train, y_train, params, model_key, data_path)

        # Evaluate
        y_pred = model.predict(X_test)
        metrics = {
            "accuracy": accuracy_score(y_test, y_pred),
            "precision": precision_score(y_test, y_pred),
            "recall": recall_score(y_test, y_pred),
            "f1_score": f1_score(y_test, y_pred)
        }
        mlflow.log_metrics(metrics)
        mlflow.set_tag("version", "1.1.0")

        # Artifacts
        cm = confusion_matrix(y_test, y_pred)
        disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=model.classes_)
        disp.plot()
        plt.savefig("confusion_matrix.png")
        mlflow.log_artifact("confusion_matrix.png")
        print(f"Run completed. Metrics: {metrics}")

if __name__ == "__main__":
    run_experiment("gb") 