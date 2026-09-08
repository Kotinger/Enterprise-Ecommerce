-- риски | fraud rate = report.kpi_fraud 
USE enterprise_ecommerce;

SELECT
  ROUND(100 * AVG(fraud_label), 2) AS fraud_pct,
  SUM(fraud_label) AS fraud_rows,
  COUNT(*) AS rows_n
FROM clean_orders;

SELECT
  payment_method,
  COUNT(DISTINCT order_key) AS orders,
  SUM(fraud_label) AS fraud_n,
  SUM(order_value) AS gmv,
  ROUND(100 * SUM(fraud_label) / COUNT(DISTINCT order_key), 2) AS fraud_pct
FROM clean_orders
GROUP BY payment_method
ORDER BY fraud_pct DESC;

SELECT
  device_type,
  COUNT(DISTINCT order_key) AS orders,
  SUM(fraud_label) AS fraud_n,
  SUM(order_value) AS gmv,
  ROUND(100 * SUM(fraud_label) / COUNT(DISTINCT order_key), 2) AS fraud_pct
FROM clean_orders
GROUP BY device_type
ORDER BY fraud_pct DESC;
