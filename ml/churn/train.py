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
PATH_CUST = DATA / "customers.csv"
PATH_BEH = DATA / "behavior.csv"
PATH_TXN = DATA / "transactions.csv"

CLIENT_COL = "customer_id"
TARGET = "churn_label"
# не в X: метка и её копии
DROP_X = [TARGET, "behavior_churn_signal", "lifetime_value", CLIENT_COL]


def load_data(path: Path)->pd.DataFrame:
    df=pd.read_csv(path)
    df.columns=df.columns.str.strip()
    return df

# агрегаты заказов на клиента
def txn_features(txn: pd.DataFrame):
    txn=txn.copy()
    txn["order_date"]=pd.to_datetime(txn["order_date"], errors="coerce")
    ref=txn["order_date"].max()
    g=txn.groupby(CLIENT_COL, as_index=False).agg(
        orders_n=("transaction_id", "nunique"),
        gmv=("order_value", "sum"),
        avg_discount=("discount_applied", "mean"),
        avg_ship_delay=("shipping_delay_days", "mean"),
        fraud_rate=("fraud_label", "mean"),
        last_order=("order_date", "max"),
        first_order=("order_date", "min"))
    g["aov"]=g["gmv"]/g["orders_n"]
    g["recency_days"]=(ref-g["last_order"]).dt.days
    g["tenure_days"]=(g["last_order"]-g["first_order"]).dt.days
    return g.drop(columns=["last_order", "first_order"]), ref

# 1 клиент = 1 строка
def make_xy(cust, beh, txn_feat, ref):
    df=cust.merge(beh, on=CLIENT_COL, how="left")
    df=df.merge(txn_feat, on=CLIENT_COL, how="left")
    df["registration_date"]=pd.to_datetime(df["registration_date"], errors="coerce")
    df["reg_tenure_days"]=(ref-df["registration_date"]).dt.days
    df=df.drop(columns=["registration_date"])
    for c in ["orders_n","gmv","aov","avg_discount","avg_ship_delay","fraud_rate","recency_days","tenure_days"]:
        if c in df.columns:
            df[c]=df[c].fillna(0)
    y=df[TARGET].astype(int)
    X=df.drop(columns=[c for c in DROP_X if c in df.columns])
    return X, y

def show_metrics(name, y_test, proba, pred):
    print("---", name, "---")
    print("ROC-AUC", round(roc_auc_score(y_test, proba), 3))
    print("confusion")
    print(confusion_matrix(y_test, pred))
    print(classification_report(y_test, pred, digits=3))

# +coef = выше шанс оттока
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
    cust=load_data(PATH_CUST)
    beh=load_data(PATH_BEH)
    txn=load_data(PATH_TXN)
    print("customers", len(cust), "churn%", round(cust[TARGET].mean()*100, 1))
    print("txn", len(txn))

    txn_feat, ref=txn_features(txn)
    X, y=make_xy(cust, beh, txn_feat, ref)
    cat_cols=[c for c in ["gender","country"] if c in X.columns]
    num_cols=[c for c in X.columns if c not in cat_cols]
    print("rows", len(X), "cat", cat_cols)

    X_train, X_test, y_train, y_test=train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y)

    # логрег — scaler, чтобы coef сравнивать
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

    # лес — scaler не нужен
    pre_rf=ColumnTransformer([
        ("num", "passthrough", num_cols),
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_cols)])
    forest=Pipeline([
        ("pre", pre_rf),
        ("clf", RandomForestClassifier(
            n_estimators=200, random_state=42, class_weight="balanced", n_jobs=-1))])
    forest.fit(X_train, y_train)
    proba_f=forest.predict_proba(X_test)[:, 1]
    pred_f=forest.predict(X_test)
    show_metrics("random forest", y_test, proba_f, pred_f)
    show_forest_imp(forest)

if __name__ == "__main__":
    main()
