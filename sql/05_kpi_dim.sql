-- маршрут A | country = report.kpi_by_country
USE enterprise_ecommerce;

SELECT
  country,
  SUM(order_value) AS gmv,
  COUNT(DISTINCT order_key) AS orders,
  SUM(order_value) / COUNT(DISTINCT order_key) AS aov
FROM clean_orders
GROUP BY country
ORDER BY gmv DESC;
