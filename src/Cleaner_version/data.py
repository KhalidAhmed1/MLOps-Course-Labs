import logging
import pandas as pd
from sklearn.utils import resample
from sklearn.model_selection import train_test_split
from sklearn.compose import make_column_transformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def rebalance(data, target_col="Exited"):
    """Downsamples the majority class to balance the dataset."""
    churn_0 = data[data[target_col] == 0]
    churn_1 = data[data[target_col] == 1]
    
    maj, min_class = (churn_0, churn_1) if len(churn_0) > len(churn_1) else (churn_1, churn_0)
    
    maj_downsampled = resample(
        maj, n_samples=len(min_class), replace=False, random_state=1234
    )
    balanced_df = pd.concat([maj_downsampled, min_class])
    logger.info(f"Data rebalanced. New shape: {balanced_df.shape}")
    return balanced_df

def preprocess_data(df, test_size=0.3):
    """Filters features, balances data, and returns transformed train/test sets."""
    cat_cols = ["Geography", "Gender"]
    num_cols = ["CreditScore", "Age", "Tenure", "Balance", "NumOfProducts", "HasCrCard", "IsActiveMember", "EstimatedSalary"]
    target = "Exited"
    
    data = df[cat_cols + num_cols + [target]]
    data_bal = rebalance(data, target)
    
    X = data_bal.drop(target, axis=1)
    y = data_bal[target]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=1912)

    transformer = make_column_transformer(
        (StandardScaler(), num_cols),
        (OneHotEncoder(handle_unknown="ignore", drop="first"), cat_cols),
        remainder="passthrough"
    )

    X_train_transformed = transformer.fit_transform(X_train)
    X_test_transformed = transformer.transform(X_test)
    
    # Convert back to DataFrame for MLflow signature tracking
    cols = transformer.get_feature_names_out()
    X_train_df = pd.DataFrame(X_train_transformed, columns=cols)
    X_test_df = pd.DataFrame(X_test_transformed, columns=cols)

    return transformer, X_train_df, X_test_df, y_train, y_test