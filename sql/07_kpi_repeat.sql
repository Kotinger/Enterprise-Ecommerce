-- маршрут B | repeat / LTV = report.kpi_repeat
USE enterprise_ecommerce;

SELECT
  COUNT(*) AS customers,
  MIN(orders) AS purchases_min,
  MAX(orders) AS purchases_max,
  ROUND(AVG(orders), 1) AS purchases_avg,
  ROUND(100.0 * SUM(orders >= 2) / COUNT(*), 1) AS repeat_pct,
  MIN(gmv) AS ltv_min,
  MAX(gmv) AS ltv_max,
  ROUND(AVG(gmv), 1) AS ltv_avg,
  ROUND(SUM(gmv), 0) AS gmv_people
FROM people;

-- медиана покупок и LTV (MySQL 8+)
SELECT 'purchases' AS metric, orders AS median_value
FROM (
  SELECT orders, ROW_NUMBER() OVER (ORDER BY orders) AS rn, COUNT(*) OVER () AS n
  FROM people
) t
WHERE rn = FLOOR((n + 1) / 2)
UNION ALL
SELECT 'ltv', gmv
FROM (
  SELECT gmv, ROW_NUMBER() OVER (ORDER BY gmv) AS rn, COUNT(*) OVER () AS n
  FROM people
) t
WHERE rn = FLOOR((n + 1) / 2);
