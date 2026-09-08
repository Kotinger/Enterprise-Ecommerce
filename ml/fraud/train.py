from pathlib import Path
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parent.parent.parent
DATA = ROOT / "data"
PATH_TXN = DATA / "transactions.csv"
PATH_CUST = DATA / "customers.csv"
PATH_PROD = DATA / "products.csv"

TARGET = "fraud_label"
# не в X: метка, id, отток/ltv клиента
DROP_X = [
    TARGET, "transaction_id", "customer_id", "product_id", "order_date",
    "churn_label", "lifetime_value", "registration_date",
]


def load_data(path: Path)->pd.DataFrame:
    df=pd.read_csv(path)
    df.columns=df.columns.str.strip()
    return df

# 1 заказ = 1 строка
def make_xy(txn, cust, prod):
    cust=cust[["customer_id","age","gender","country","loyalty_score"]]
    prod=prod[["product_id","category","margin_percentage","popularity_score"]]
    df=txn.merge(cust, on="customer_id", how="left")
    df=df.merge(prod, on="product_id", how="left")
    y=df[TARGET].astype(int)
    X=df.drop(columns=[c for c in DROP_X if c in df.columns])
    return X, y

def show_metrics(name, y_test, proba, pred):
    print("---", name, "---")
    print("ROC-AUC", round(roc_auc_score(y_test, proba), 3))
    print("confusion")
    print(confusion_matrix(y_test, pred))
    print(classification_report(y_test, pred, digits=3))

def show_logreg_imp(model, n=12):
    names=model.named_steps["pre"].get_feature_names_out()
    coefs=model.named_steps["clf"].coef_[0]
    imp=pd.DataFrame({"feature": names, "coef": coefs})
    imp["abs"]=imp["coef"].abs()
    imp=imp.sort_values("abs", ascending=False)
    print("--- logreg importance ---")
    print(imp.head(n)[["feature","coef"]].to_string(index=False))

def show_forest_imp(model, n=12):
    names=model.named_steps["pre"].get_feature_names_out()
    imp=pd.DataFrame({
        "feature": names,
        "importance": model.named_steps["clf"].feature_importances_})
    imp=imp.sort_values("importance", ascending=False)
    print("--- forest importance ---")
    print(imp.head(n).to_string(index=False))

def main()->None:
    txn=load_data(PATH_TXN)
    cust=load_data(PATH_CUST)
    prod=load_data(PATH_PROD)
    print("txn", len(txn), "fraud%", round(txn[TARGET].mean()*100, 2))

    X, y=make_xy(txn, cust, prod)
    cat_cols=[c for c in ["payment_method","device_type","gender","country","category"] if c in X.columns]
    num_cols=[c for c in X.columns if c not in cat_cols]
    print("rows", len(X), "cat", cat_cols)

    X_train, X_test, y_train, y_test=train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y)

    pre_lr=ColumnTransformer([
        ("num", StandardScaler(), num_cols),
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_cols)])
    logreg=Pipeline([
        ("pre", pre_lr),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced"))])
    logreg.fit(X_train, y_train)
    proba=logreg.predict_proba(X_test)[:, 1]
    pred=logreg.predict(X_test)
    show_metrics("logreg", y_test, proba, pred)
    show_logreg_imp(logreg)

    pre_rf=ColumnTransformer([
        ("num", "passthrough", num_cols),
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_cols)])
    forest=Pipeline([
        ("pre", pre_rf),
        ("clf", RandomForestClassifier(
            n_estimators=100, random_state=42, class_weight="balanced", n_jobs=-1))])
    forest.fit(X_train, y_train)
    proba_f=forest.predict_proba(X_test)[:, 1]
    pred_f=forest.predict(X_test)
    show_metrics("random forest", y_test, proba_f, pred_f)
    show_forest_imp(forest)

if __name__ == "__main__":
    main()
