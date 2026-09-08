-- маршрут A | totals = report.kpi_totals
USE enterprise_ecommerce;

SELECT
  SUM(order_value) AS gmv,
  COUNT(DISTINCT order_key) AS orders,
  SUM(order_value) / COUNT(DISTINCT order_key) AS aov
FROM clean_orders;
