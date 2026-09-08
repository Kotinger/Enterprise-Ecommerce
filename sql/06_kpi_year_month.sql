-- маршрут A | год × месяц = report.kpi_year_month
USE enterprise_ecommerce;

SELECT
  YEAR(order_date) AS year,
  MONTH(order_date) AS month,
  SUM(order_value) AS gmv,
  COUNT(DISTINCT order_key) AS orders,
  SUM(order_value) / COUNT(DISTINCT order_key) AS aov
FROM clean_orders
GROUP BY YEAR(order_date), MONTH(order_date)
ORDER BY year, month;
