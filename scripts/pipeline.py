from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PATH_TXN = ROOT / "data" / "transactions.csv"
PATH_CUST = ROOT / "data" / "customers.csv"
PATH_PROD = ROOT / "data" / "products.csv"
PATH_BEH = ROOT / "data" / "behavior.csv"

ORDER_COL = "transaction_id"
ORDER_KEY = "order_key"
DATE_COL = "order_date"
MONEY_COL = "order_value"
CLIENT_COL = "customer_id"
PRODUCT_COL = "product_id"

DIM_COUNTRY_COL = "country"
DIM_CATEGORY_COL = "category"


def load_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    #print("===", path.name, "===")
    #print("shape", df.shape)
    #print("columns", df.columns.tolist())
    #print("dtypes", df.dtypes)
    #print("isna",df.isna().sum())
    #print("duplicated", df.duplicated().sum())
    #print(df.head(3))
    return df


def check_grain(df: pd.DataFrame) -> str:
    rows = len(df)
    orders = df[ORDER_COL].nunique()
    if rows > orders * 1.2:
        grain = "line"
    else:
        grain = "order"
    #print("rows", rows, "orders", orders, "->", grain)
    return grain


def prepare_types(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df[ORDER_COL] = df[ORDER_COL].astype(str).str.strip()
    df[CLIENT_COL] = df[CLIENT_COL].astype(str).str.strip()
    df[PRODUCT_COL] = df[PRODUCT_COL].astype(str).str.strip()

    # order_value уже float to_numeric на всякий
    df[MONEY_COL] = pd.to_numeric(df[MONEY_COL], errors="coerce")

    df[DATE_COL] = pd.to_datetime(df[DATE_COL], dayfirst=False, errors="coerce")

    #print("money dtype", df[MONEY_COL].dtype)
    #print("money sum", df[MONEY_COL].sum(), "NaN", df[MONEY_COL].isna().sum())
    #print(
    #    "money min/median/max",
    #    df[MONEY_COL].min(),
    #    df[MONEY_COL].median(),
    #    df[MONEY_COL].max(),
    #)
    #print("money <0", int((df[MONEY_COL] < 0).sum()))
    #print("dates", df[DATE_COL].min(), "->", df[DATE_COL].max())
    #print("NaT", df[DATE_COL].isna().sum())
    return df


def build_clean(df: pd.DataFrame) -> pd.DataFrame:
    # отмен нет; money <0 = 0 → фильтр >0 не нужен
    clean = df.copy()
    #print("старт", len(clean))
    #print("gmv", clean[MONEY_COL].sum(), "rows", len(clean))
    #print("money median", clean[MONEY_COL].median())
    return clean

#если возникает вопрос почему я это делаю в каждом датасете, то ответ прост: 
# 1. я хочу убедиться что данные в каждом датасете чистые и корректные, и что после очистки не потеряно слишком много информации;
# 2. я хочу понять структуру данных и сам датасет, чтобы в дальнейшем было проще работать с ним и делать анализ!!!
# * в среднем на понимание такого датасета уходит 2-3 часа.
def sanity_check(raw: pd.DataFrame, clean: pd.DataFrame) -> None:
    print("--- sanity ---")
    drop_pct = (1 - len(clean) / len(raw)) * 100
    print("rows", len(raw), "->", len(clean))
    print("отвал строк%", round(drop_pct, 2))
    print("orders", raw[ORDER_COL].nunique(), "->", clean[ORDER_COL].nunique())
    print("gmv", clean[MONEY_COL].sum())
    print(
        "money min/median/max",
        clean[MONEY_COL].min(),
        clean[MONEY_COL].median(),
        clean[MONEY_COL].max(),
    )
    print("даты", clean[DATE_COL].min(), "->", clean[DATE_COL].max())
    print("полных дублей строк", int(clean.duplicated().sum()))
    print("клиентов в clean", clean[CLIENT_COL].nunique())
    print("уникальные товары в clean", clean[PRODUCT_COL].nunique())
    
def add_keys(clean: pd.DataFrame) -> pd.DataFrame:
    clean = clean.copy()
    print("---keys---")
    header = [DATE_COL, CLIENT_COL]
    clean[ORDER_KEY] = clean[ORDER_COL].astype(str)
    check = clean.groupby(ORDER_COL)[header].nunique()
    bad = int((check > 1).any(axis=1).sum())
    print("плохих заказов", bad)
    print("ключей", clean[ORDER_KEY].nunique())
    return clean

#чтобы не дублировать в join_dims
def prepare_dim_keys(df: pd.DataFrame, key_col: str) -> pd.DataFrame:
    df = df.copy()
    df[key_col] = df[key_col].astype(str).str.strip()
    return df

def join_dims(
    clean: pd.DataFrame,
    customers: pd.DataFrame,
    products: pd.DataFrame,
    behavior: pd.DataFrame,
) -> pd.DataFrame:
    print("--- join ---")
    gmv_before = clean[MONEY_COL].sum()
    rows_before = len(clean)

    customers = prepare_dim_keys(customers, CLIENT_COL)
    products = prepare_dim_keys(products, PRODUCT_COL)
    behavior = prepare_dim_keys(behavior, CLIENT_COL)

    # dim: 1 id = 1 строка, иначе left merge раздует GMV
    dup_c = int(customers[CLIENT_COL].duplicated().sum())
    dup_p = int(products[PRODUCT_COL].duplicated().sum())
    dup_b = int(behavior[CLIENT_COL].duplicated().sum())
    print("дубли id customers/products/behavior", dup_c, dup_p, dup_b)

    # orphan = ключ на факте, которого нет в dim
    orphan_c = ~clean[CLIENT_COL].isin(customers[CLIENT_COL])
    orphan_p = ~clean[PRODUCT_COL].isin(products[PRODUCT_COL])
    orphan_b = ~clean[CLIENT_COL].isin(behavior[CLIENT_COL])
    print("orphan customers", int(orphan_c.sum()))
    print("orphan products", int(orphan_p.sum()))
    print("orphan behavior", int(orphan_b.sum()))

    out = clean.merge(customers, on=CLIENT_COL, how="left")
    out = out.merge(products, on=PRODUCT_COL, how="left")
    out = out.merge(behavior, on=CLIENT_COL, how="left")

    print("rows", rows_before, "->", len(out))
    print("gmv", gmv_before, "->", out[MONEY_COL].sum())
    print(
        "новые поля",
        [c for c in ["country", "category", "churn_label", "margin_percentage"] if c in out.columns],
    )
    return out

def build_people(clean: pd.DataFrame) -> pd.DataFrame:
    print("--- people ---")
    no_id = clean[CLIENT_COL].isna().sum()
    print("нет id", no_id)
    base = clean.dropna(subset=[CLIENT_COL])
    people = base.groupby(CLIENT_COL, as_index=False).agg(
        gmv=(MONEY_COL, "sum"),
        orders=(ORDER_COL, "nunique"),
        first_order=(DATE_COL, "min"),
    )
    print("ltv min/median/max",
          people["gmv"].min(),
          people["gmv"].median(),
          people["gmv"].max())
    print("клиентов", len(people), "повторных", int((people["orders"] >= 2).sum()))
    print("repeat%", round((people["orders"] >= 2).mean() * 100, 1))
    print("gmv people", people["gmv"].sum())
    return people


def save_tables(clean: pd.DataFrame, people: pd.DataFrame | None = None) -> None:
    print("--- save ---")
    out_dir = ROOT / "data" / "processed"
    out_dir.mkdir(parents=True, exist_ok=True)

    clean.to_parquet(out_dir / "clean.parquet", index=False)
    if people is not None:
        people.to_parquet(out_dir / "people.parquet", index=False)

    back = pd.read_parquet(out_dir / "clean.parquet")
  


def main() -> None:
    raw = load_data(PATH_TXN)
    customers = load_data(PATH_CUST)
    products = load_data(PATH_PROD)
    behavior = load_data(PATH_BEH)

    check_grain(raw)
    typed = prepare_types(raw)
    clean = build_clean(typed)
    sanity_check(raw, clean)
    clean = add_keys(clean)
    clean = join_dims(clean, customers, products, behavior)
    people = build_people(clean)
    save_tables(clean, people)
    


if __name__ == "__main__":
    main()
