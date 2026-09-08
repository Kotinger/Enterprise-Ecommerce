-- sanity = report.kpi_totals / якорь pipeline
-- orders = COUNT(DISTINCT order_key)
USE enterprise_ecommerce;

SELECT COUNT(*) AS rows_n FROM clean_orders;

SELECT
  COUNT(DISTINCT order_key) AS orders_n,
  SUM(order_value) AS gmv,
  SUM(profit) AS profit,
  MIN(order_date) AS date_min,
  MAX(order_date) AS date_max,
  COUNT(DISTINCT customer_id) AS customers_n
FROM clean_orders;

SELECT COUNT(*) AS people_n, SUM(gmv) AS gmv_people FROM people;
