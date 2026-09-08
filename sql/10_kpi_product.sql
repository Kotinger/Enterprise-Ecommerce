-- маршрут C | margin / top SKU / category = report.kpi_margin + kpi_top + kpi_cat
USE enterprise_ecommerce;

-- общая маржа
SELECT
  COUNT(DISTINCT product_id) AS sku,
  SUM(order_value) AS gmv,
  SUM(profit) AS profit,
  ROUND(100 * SUM(profit) / SUM(order_value), 1) AS margin_pct
FROM clean_orders;

-- топ SKU по GMV
SELECT
  product_id,
  SUM(order_value) AS gmv,
  COUNT(DISTINCT order_key) AS orders,
  SUM(profit) AS profit,
  SUM(order_value) / COUNT(DISTINCT order_key) AS aov,
  ROUND(100 * SUM(profit) / SUM(order_value), 1) AS margin_pct
FROM clean_orders
GROUP BY product_id
ORDER BY gmv DESC
LIMIT 10;

-- по категориям
SELECT
  category,
  SUM(order_value) AS gmv,
  COUNT(DISTINCT order_key) AS orders,
  SUM(profit) AS profit,
  SUM(order_value) / COUNT(DISTINCT order_key) AS aov,
  ROUND(100 * SUM(profit) / SUM(order_value), 1) AS margin_pct
FROM clean_orders
GROUP BY category
ORDER BY gmv DESC;
