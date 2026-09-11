from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT/"data"/"processed"

ORDER_COL = "transaction_id"
ORDER_KEY = "order_key"
DATE_COL = "order_date"
MONEY_COL = "order_value"
CLIENT_COL = "customer_id"
PRODUCT_COL = "product_id"
DIM_COUNTRY_COL = "country"
DIM_CATEGORY_COL = "category"
MARGIN_PCT_COL = "margin_percentage"
FLAG_COL = "churn_label"
FRAUD_COL = "fraud_label"
PAYMENT_COL = "payment_method"
DEVICE_COL = "device_type"

def load_tables():
    clean = pd.read_parquet(OUT_DIR/"clean.parquet")
    people = pd.read_parquet(OUT_DIR/"people.parquet")
    return clean, people

#Маршрут A — продажи: GMV, orders, AOV, country, год×месяц
# totals: общий GMV / заказы / AOV + период
def kpi_totals(clean: pd.DataFrame)-> None:
    gmv = clean[MONEY_COL].sum()
    orders = clean[ORDER_KEY].nunique()
    aov = gmv / orders
    print("gmv", gmv, "orders", orders, "aov", aov)
    print("money min/median/max", clean[MONEY_COL].min(), clean[MONEY_COL].median(), clean[MONEY_COL].max())
    print("period", clean[DATE_COL].min(), "->", clean[DATE_COL].max())

# срез продаж по стране
def kpi_by_country(clean: pd.DataFrame)-> pd.DataFrame:
    check_country = clean.groupby(DIM_COUNTRY_COL, as_index=False).agg(
        gmv=(MONEY_COL, "sum"),
        orders=(ORDER_KEY, "nunique"))
    check_country["aov"] = check_country["gmv"] / check_country["orders"]
    check_country = check_country.sort_values("gmv", ascending=False)
    print(check_country)
    return check_country

# динамика GMV / orders / AOV по году и месяцу
def kpi_year_month(clean: pd.DataFrame)-> pd.DataFrame:
    y_m = clean.copy()
    y_m["month"] = y_m[DATE_COL].dt.month
    y_m["year"] = y_m[DATE_COL].dt.year
    chek_y_m = y_m.groupby(["year", "month"], as_index=False).agg(
        gmv=(MONEY_COL, "sum"),
        orders=(ORDER_KEY, "nunique"))
    chek_y_m["aov"] = chek_y_m["gmv"] / chek_y_m["orders"]
    chek_y_m = chek_y_m.sort_values(["year", "month"])
    print(chek_y_m.head(10))
    return chek_y_m

#Маршрут B — клиенты: repeat, LTV, retention, RFM, churn_label
# repeat% + LTV (из people)
def kpi_repeat(people: pd.DataFrame)-> None:
    print("customer", len(people))
    print("покупок min/median/max", int(people["orders"].min()), people["orders"].median(), int(people["orders"].max()))
    print("repeat>=2", int((people["orders"] >= 2).sum()))
    repeat_pct = (people["orders"] >= 2).mean() * 100
    print("repeat%", round(repeat_pct, 1))
    print("gmv people", people["gmv"].sum())
    print("ltv min/median/max", people["gmv"].min(), people["gmv"].median(), people["gmv"].max())

# когорты + retention (только clean)
def kpi_retention(clean: pd.DataFrame)-> None:
    orders = clean.groupby([CLIENT_COL, ORDER_KEY], as_index=False).agg(
        order_date=(DATE_COL, "min"))
    orders["order_month"] = orders["order_date"].dt.to_period("M")
    first = orders.groupby(CLIENT_COL)["order_month"].min()
    first = first.rename("cohort")
    orders = orders.join(first, on=CLIENT_COL)
    orders["period_n"] = orders["order_month"].astype(int) - orders["cohort"].astype(int)
    size = orders.groupby("cohort")[CLIENT_COL].nunique()
    active = orders.groupby(["cohort", "period_n"])[CLIENT_COL].nunique()
    ret = active.div(size, level=0).unstack(fill_value=0)
    print("cohort", len(size))
    print("min/median/max", int(size.min()), float(size.median()), int(size.max()))
    if 1 in ret.columns:
        print("retention period_n=1 median", round(float(ret[1].median()), 3))
    print(ret.iloc[:6, :8].round(3))

# RFM-сегменты: R из clean, F/M из people
def kpi_rfm(clean: pd.DataFrame, people: pd.DataFrame)-> pd.DataFrame:
    ref = clean[DATE_COL].max()
    last = clean.groupby(CLIENT_COL)[DATE_COL].max()
    last = last.rename("last_order")
    rfm = people.merge(last, left_on=CLIENT_COL, right_index=True, how="left")
    rfm["recency"] = (ref - rfm["last_order"]).dt.days
    rfm["frequency"] = rfm["orders"]
    rfm["monetary"] = rfm["gmv"]
    rfm["R"] = pd.qcut(rfm["recency"], 3, labels=[3, 2, 1], duplicates="drop")
    rfm["F"] = pd.qcut(rfm["frequency"].rank(method="first"), 3, labels=[1, 2, 3], duplicates="drop")
    rfm["M"] = pd.qcut(rfm["monetary"].rank(method="first"), 3, labels=[1, 2, 3], duplicates="drop")
    rfm["segment"] = rfm["R"].astype(str) + rfm["F"].astype(str) + rfm["M"].astype(str)
    print("recency day min/median/max", int(rfm["recency"].min()), float(rfm["recency"].median()), int(rfm["recency"].max()))
    print(rfm["segment"].value_counts().head(10))
    top = rfm[rfm["segment"] == "333"]
    if len(top) > 0:
        share = top["gmv"].sum() / rfm["gmv"].sum() * 100
        print("333", len(top), "gmv%", round(share, 1))
    cold = rfm[rfm["R"].astype(int) == 1]
    print("R=1", len(cold), "castomers%", round(len(cold) / len(rfm) * 100, 1), "gmv%", round(cold["gmv"].sum() / rfm["gmv"].sum() * 100, 1))
    return rfm

def save_people_rfm(people: pd.DataFrame, rfm: pd.DataFrame)-> None:
    # дописываем segment/R из kpi_rfm в people.parquet для MySQL/PBI
    out = people.merge(rfm[[CLIENT_COL, "segment", "R"]], on=CLIENT_COL, how="left")
    out["R"] = out["R"].astype(int)
    out["segment"] = out["segment"].astype(str)
    out.to_parquet(OUT_DIR/"people.parquet", index=False)
    print("saved people + rfm", OUT_DIR/"people.parquet")

# срез people по churn_label
def kpi_by_flag(clean: pd.DataFrame, people: pd.DataFrame)-> pd.DataFrame:
    mixed = clean.groupby(CLIENT_COL)[FLAG_COL].nunique()
    mixed_n = int((mixed > 1).sum())
    print("клиентов со смешанным", FLAG_COL, mixed_n)

    flag = clean.groupby(CLIENT_COL, as_index=False)[FLAG_COL].first()
    p = people.merge(flag, on=CLIENT_COL, how="left")

    gmv_all = p["gmv"].sum()
    out = p.groupby(FLAG_COL, as_index=False).agg(
        customers=(CLIENT_COL, "count"),
        purchases_median=("orders", "median"),
        ltv_median=("gmv", "median"),
        gmv=("gmv", "sum"))
    out["customers_pct"] = (out["customers"] / out["customers"].sum() * 100).round(1)
    out["gmv_pct"] = (out["gmv"] / gmv_all * 100).round(1)
    print(out)
    return out

#Маршрут C — продукт: маржа, топ SKU, категории
# общая маржа = sum(profit) / sum(GMV)
def kpi_margin(clean: pd.DataFrame)-> None:
    clean = clean.copy()
    clean["profit"] = clean[MONEY_COL] * clean[MARGIN_PCT_COL] / 100
    profit = clean["profit"].sum()
    gmv = clean[MONEY_COL].sum()
    margin = round(profit / gmv * 100, 1)
    sku = clean[PRODUCT_COL].nunique()
    print("sku", sku)
    print("profit", profit)
    print("margin%", margin)

# топ SKU по GMV + AOV + маржа
def kpi_top(clean: pd.DataFrame)-> pd.DataFrame:
    clean = clean.copy()
    clean["profit"] = clean[MONEY_COL] * clean[MARGIN_PCT_COL] / 100
    top_p = clean.groupby(PRODUCT_COL, as_index=False).agg(
        gmv=(MONEY_COL, "sum"),
        orders=(ORDER_KEY, "nunique"),
        profit=("profit", "sum"))
    top_p["aov"] = top_p["gmv"] / top_p["orders"]
    top_p["margin%"] = top_p["profit"] / top_p["gmv"] * 100
    top_p = top_p.sort_values("gmv", ascending=False)
    print(top_p.head(10))
    return top_p

# маржа и AOV по категориям
def kpi_cat(clean: pd.DataFrame)-> pd.DataFrame:
    clean = clean.copy()
    clean["profit"] = clean[MONEY_COL] * clean[MARGIN_PCT_COL] / 100
    cat = clean.groupby(DIM_CATEGORY_COL, as_index=False).agg(
        gmv=(MONEY_COL, "sum"),
        orders=(ORDER_KEY, "nunique"),
        profit=("profit", "sum"))
    cat["aov"] = cat["gmv"] / cat["orders"]
    cat["margin%"] = cat["profit"] / cat["gmv"] * 100
    cat = cat.sort_values("gmv", ascending=False)
    print(cat)
    return cat

#Риски — не маршрут из тройки: fraud rate по payment / device
# доля fraud_label overall + срезы
def kpi_fraud(clean: pd.DataFrame)-> None:
    rate = clean[FRAUD_COL].mean() * 100
    print("fraud%", round(rate, 2))
    print("fraud rows", int(clean[FRAUD_COL].sum()), "from", len(clean))
    by_pay = clean.groupby(PAYMENT_COL, as_index=False).agg(
        orders=(ORDER_KEY, "nunique"),
        fraud_n=(FRAUD_COL, "sum"),
        gmv=(MONEY_COL, "sum"))
    by_pay["fraud%"] = (by_pay["fraud_n"] / by_pay["orders"] * 100).round(2)
    by_pay = by_pay.sort_values("fraud%", ascending=False)
    print(by_pay)
    by_dev = clean.groupby(DEVICE_COL, as_index=False).agg(
        orders=(ORDER_KEY, "nunique"),
        fraud_n=(FRAUD_COL, "sum"),
        gmv=(MONEY_COL, "sum"))
    by_dev["fraud%"] = (by_dev["fraud_n"] / by_dev["orders"] * 100).round(2)
    by_dev = by_dev.sort_values("fraud%", ascending=False)
    print(by_dev)

def main()-> None:
    clean, people = load_tables()
    #Маршрут A
    kpi_totals(clean)
    kpi_by_country(clean)
    kpi_year_month(clean)
    #Маршрут B
    kpi_repeat(people)
    kpi_retention(clean)
    rfm = kpi_rfm(clean, people)
    save_people_rfm(people, rfm)
    kpi_by_flag(clean, people)
    #Маршрут C
    kpi_margin(clean)
    kpi_top(clean)
    kpi_cat(clean)
    #Риски (доп. срез, не маршрут)
    kpi_fraud(clean)

if __name__ == "__main__":
    main()
