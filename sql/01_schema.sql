-- Active: 1788868810471@@127.0.0.1@3306@enterprise_ecommerce
-- Enterprise Ecommerce | зерно: order (transaction_id ≈ order_key)
-- Маршруты A+B+C + риски (fraud) + флаг churn_label
CREATE DATABASE IF NOT EXISTS enterprise_ecommerce
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE enterprise_ecommerce;

DROP TABLE IF EXISTS people;
DROP TABLE IF EXISTS clean_orders;

-- факт после join dims (только поля под KPI / PBI)
CREATE TABLE clean_orders (
  transaction_id VARCHAR(50) NOT NULL,
  order_key VARCHAR(50) NOT NULL,
  customer_id VARCHAR(50) NOT NULL,
  product_id VARCHAR(50) NULL,
  order_date DATETIME NOT NULL,
  order_value DECIMAL(14, 2) NOT NULL,
  profit DECIMAL(14, 4) NULL,
  country VARCHAR(100) NULL,
  category VARCHAR(100) NULL,
  margin_percentage DECIMAL(8, 2) NULL,
  churn_label TINYINT NULL,
  fraud_label TINYINT NULL,
  payment_method VARCHAR(50) NULL,
  device_type VARCHAR(50) NULL,
  INDEX idx_order_key (order_key),
  INDEX idx_customer (customer_id),
  INDEX idx_date (order_date),
  INDEX idx_country (country),
  INDEX idx_product (product_id)
) ENGINE=InnoDB;

-- 1 клиент = 1 строка (people.parquet + churn с clean)
CREATE TABLE people (
  customer_id VARCHAR(50) NOT NULL PRIMARY KEY,
  gmv DECIMAL(14, 2) NOT NULL,
  orders INT NOT NULL,
  first_order DATETIME NOT NULL,
  churn_label TINYINT NULL,
  segment VARCHAR(10) NULL,
  R TINYINT NULL
) ENGINE=InnoDB;
