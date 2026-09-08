-- маршрут B | RFM = report.kpi_rfm
-- R от последней покупки; опора = MAX(order_date), не NOW()
USE enterprise_ecommerce;

WITH last_buy AS (
  SELECT customer_id, MAX(order_date) AS last_order
  FROM clean_orders
  GROUP BY customer_id
),
base AS (
  SELECT
    p.customer_id,
    p.orders AS frequency,
    p.gmv AS monetary,
    TIMESTAMPDIFF(DAY, l.last_order, (SELECT MAX(order_date) FROM clean_orders)) AS recency
  FROM people p
  JOIN last_buy l ON l.customer_id = p.customer_id
),
scored AS (
  SELECT
    customer_id,
    recency,
    frequency,
    monetary,
    4 - NTILE(3) OVER (ORDER BY recency) AS r_score,
    NTILE(3) OVER (ORDER BY frequency) AS f_score,
    NTILE(3) OVER (ORDER BY monetary) AS m_score
  FROM base
),
seg AS (
  SELECT
    *,
    CONCAT(r_score, f_score, m_score) AS segment
  FROM scored
)
SELECT segment, COUNT(*) AS customers, ROUND(SUM(monetary), 0) AS gmv
FROM seg
GROUP BY segment
ORDER BY customers DESC
LIMIT 10;

SELECT
  MIN(recency) AS recency_min,
  AVG(recency) AS recency_avg,
  MAX(recency) AS recency_max
FROM (
  SELECT TIMESTAMPDIFF(
    DAY,
    last_order,
    (SELECT MAX(order_date) FROM clean_orders)
  ) AS recency
  FROM (
    SELECT customer_id, MAX(order_date) AS last_order
    FROM clean_orders
    GROUP BY customer_id
  ) t
) r;

-- чемпионы 333 и остывшие R=1
WITH last_buy AS (
  SELECT customer_id, MAX(order_date) AS last_order
  FROM clean_orders
  GROUP BY customer_id
),
base AS (
  SELECT
    p.customer_id,
    p.orders AS frequency,
    p.gmv AS monetary,
    TIMESTAMPDIFF(DAY, l.last_order, (SELECT MAX(order_date) FROM clean_orders)) AS recency
  FROM people p
  JOIN last_buy l ON l.customer_id = p.customer_id
),
scored AS (
  SELECT
    *,
    4 - NTILE(3) OVER (ORDER BY recency) AS r_score,
    NTILE(3) OVER (ORDER BY frequency) AS f_score,
    NTILE(3) OVER (ORDER BY monetary) AS m_score
  FROM base
)
SELECT
  SUM(CONCAT(r_score, f_score, m_score) = '333') AS champions_333,
  ROUND(100 * SUM(CASE WHEN CONCAT(r_score, f_score, m_score) = '333' THEN monetary ELSE 0 END) / SUM(monetary), 1) AS champions_gmv_pct,
  SUM(r_score = 1) AS cold_r1,
  ROUND(100 * SUM(CASE WHEN r_score = 1 THEN monetary ELSE 0 END) / SUM(monetary), 1) AS cold_gmv_pct
FROM scored;
