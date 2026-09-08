from __future__ import annotations
import os
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "processed"

# в parquet уже snake_case — берём только нужное для KPI
CLEAN_COLS = [
    "transaction_id",
    "order_key",
    "customer_id",
    "product_id",
    "order_date",
    "order_value",
    "country",
    "category",
    "margin_percentage",
    "churn_label",
    "fraud_label",
    "payment_method",
    "device_type",
]

PEOPLE_COLS = ["customer_id", "gmv", "orders", "first_order", "segment", "R"]
FLAG_COL = "churn_label"
MONEY_COL = "order_value"
CLIENT_COL = "customer_id"
MARGIN_PCT_COL = "margin_percentage"

DB_USER = os.getenv("MYSQL_USER", "root")
DB_HOST = os.getenv("MYSQL_HOST", "localhost")
DB_NAME = os.getenv("MYSQL_DATABASE", "enterprise_ecommerce")


def read_password() -> str:
    env = os.environ.get("MYSQL_PASSWORD")
    if env:
        return env.strip()
    pass_file = ROOT / "pass.txt"
    if pass_file.exists():
        for line in pass_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                return line
    raise SystemExit("Нет пароля: MYSQL_PASSWORD или pass.txt")


def main() -> None:
    url = f"mysql+pymysql://{DB_USER}:{read_password()}@{DB_HOST}/{DB_NAME}"
    engine = create_engine(url)

    clean = pd.read_parquet(OUT_DIR / "clean.parquet")
    people = pd.read_parquet(OUT_DIR / "people.parquet")

    missing = [c for c in CLEAN_COLS if c not in clean.columns]
    if missing:
        raise SystemExit(f"В clean.parquet нет колонок: {missing}")
    if "segment" not in people.columns:
        raise SystemExit("В people.parquet нет segment — сначала: python scripts/report.py")

    clean = clean[CLEAN_COLS].copy()
    clean["profit"] = clean[MONEY_COL] * clean[MARGIN_PCT_COL] / 100

    people = people[[c for c in PEOPLE_COLS if c in people.columns]].copy()
    if FLAG_COL in clean.columns:
        flag = clean.groupby(CLIENT_COL, as_index=False)[FLAG_COL].first()
        people = people.merge(flag, on=CLIENT_COL, how="left")

    with engine.begin() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}`"))
        conn.execute(text(f"USE `{DB_NAME}`"))

    clean.to_sql("clean_orders", engine, if_exists="replace", index=False, chunksize=5000)
    people.to_sql("people", engine, if_exists="replace", index=False, chunksize=5000)

    print("people cols", people.columns.tolist())


if __name__ == "__main__":
    main()
