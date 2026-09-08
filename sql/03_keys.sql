-- ключи: есть order_key; проверяем шапку и churn
USE enterprise_ecommerce;

SHOW TABLES;
DESCRIBE clean_orders;
DESCRIBE people;

SELECT transaction_id, order_key, customer_id, order_value, order_date, country
FROM clean_orders
LIMIT 5;

SELECT customer_id, gmv, orders, first_order, churn_label
FROM people
LIMIT 5;

-- плохие заказы: у одного order_key разные клиент/дата
SELECT COUNT(*) AS bad_orders
FROM (
  SELECT order_key
  FROM clean_orders
  GROUP BY order_key
  HAVING COUNT(DISTINCT customer_id) > 1
      OR COUNT(DISTINCT DATE(order_date)) > 1
) t;

-- у клиента один churn_label?
SELECT COUNT(*) AS mixed_churn
FROM (
  SELECT customer_id
  FROM clean_orders
  GROUP BY customer_id
  HAVING COUNT(DISTINCT churn_label) > 1
) t;
