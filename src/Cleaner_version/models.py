import mlflow
import mlflow.sklearn
import mlflow.data

def log_and_train(model, X_train, y_train, params, model_name, data_path):
    """Generic wrapper to train any model and log metadata to MLflow."""
    model.set_params(**params)
    model.fit(X_train, y_train)

    # Log Params & Metrics
    mlflow.log_params(params)
    mlflow.log_param("model_type", model_name)

    # Log Input Data Context
    dataset = mlflow.data.from_pandas(X_train, source=data_path, name="training_data")
    mlflow.log_input(dataset, context="training")

    # Log Model with Signature
    signature = mlflow.models.infer_signature(X_train, model.predict(X_train))
    mlflow.sklearn.log_model(model, artifact_path="model", signature=signature)
    
    return model