-- маршрут B | retention = report.kpi_retention
-- визит = customer_id + order_key (min даты)
USE enterprise_ecommerce;

WITH visits AS (
  SELECT
    customer_id,
    order_key,
    MIN(order_date) AS order_date
  FROM clean_orders
  GROUP BY customer_id, order_key
),
purchases AS (
  SELECT
    customer_id,
    DATE_FORMAT(order_date, '%Y-%m-01') AS order_month
  FROM visits
),
firsts AS (
  SELECT customer_id, MIN(order_month) AS cohort
  FROM purchases
  GROUP BY customer_id
),
labeled AS (
  SELECT
    p.customer_id,
    f.cohort,
    TIMESTAMPDIFF(MONTH, f.cohort, p.order_month) AS period_n
  FROM purchases p
  JOIN firsts f ON f.customer_id = p.customer_id
),
size AS (
  SELECT cohort, COUNT(DISTINCT customer_id) AS cohort_size
  FROM firsts
  GROUP BY cohort
),
active AS (
  SELECT cohort, period_n, COUNT(DISTINCT customer_id) AS active_n
  FROM labeled
  GROUP BY cohort, period_n
)
SELECT
  a.cohort,
  a.period_n,
  a.active_n,
  s.cohort_size,
  ROUND(a.active_n / s.cohort_size, 3) AS retention
FROM active a
JOIN size s ON s.cohort = a.cohort
WHERE a.period_n BETWEEN 0 AND 7
ORDER BY a.cohort, a.period_n
LIMIT 50;

-- сводка размеров когорт
SELECT
  COUNT(*) AS cohorts_n,
  MIN(cohort_size) AS size_min,
  MAX(cohort_size) AS size_max
FROM (
  SELECT COUNT(DISTINCT customer_id) AS cohort_size
  FROM people
  GROUP BY DATE_FORMAT(first_order, '%Y-%m-01')
) t;
