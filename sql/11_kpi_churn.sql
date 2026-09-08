-- доп. срез | churn_label = report.kpi_by_flag
USE enterprise_ecommerce;

SELECT
  churn_label,
  COUNT(*) AS customers,
  ROUND(AVG(orders), 1) AS purchases_avg,
  ROUND(SUM(gmv), 0) AS gmv,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS customers_pct,
  ROUND(100.0 * SUM(gmv) / SUM(SUM(gmv)) OVER (), 1) AS gmv_pct
FROM people
GROUP BY churn_label
ORDER BY churn_label;
