CREATE SCHEMA IF NOT EXISTS `project-bad2bf27-d410-468a-acf.weather_lake`
OPTIONS(location="US");

CREATE SCHEMA IF NOT EXISTS `project-bad2bf27-d410-468a-acf.weather_mart`
OPTIONS(location="US");

CREATE OR REPLACE EXTERNAL TABLE `project-bad2bf27-d410-468a-acf.weather_lake.silver_weather_ext`
OPTIONS (
  format = 'PARQUET',
  uris = ['gs://weather-data-dakshin-2026/silver/*']
);

CREATE OR REPLACE TABLE `project-bad2bf27-d410-468a-acf.weather_mart.gold_daily_city_summary`
PARTITION BY summary_date
CLUSTER BY city AS
WITH base AS (
SELECT
DATE(TIMESTAMP(event_timestamp_utc)) AS summary_date,
city,
country,
temperature,
humidity,
pressure,
wind_speed,
weather
FROM `project-bad2bf27-d410-468a-acf.weather_lake.silver_weather_ext`
),
weather_ranked AS (
SELECT
summary_date,
city,
country,
weather,
COUNT(*) AS cnt,
ROW_NUMBER() OVER (
PARTITION BY summary_date, city, country
ORDER BY COUNT(*) DESC
) AS rn
FROM base
GROUP BY summary_date, city, country, weather
)
SELECT
b.summary_date,
b.city,
b.country,
COUNT(*) AS readings_count,
ROUND(AVG(b.temperature), 2) AS avg_temperature,
ROUND(MIN(b.temperature), 2) AS min_temperature,
ROUND(MAX(b.temperature), 2) AS max_temperature,
ROUND(AVG(b.humidity), 2) AS avg_humidity,
ROUND(AVG(b.pressure), 2) AS avg_pressure,
ROUND(AVG(b.wind_speed), 2) AS avg_wind_speed,
ANY_VALUE(w.weather) AS dominant_weather,
CURRENT_TIMESTAMP() AS generated_at_utc
FROM base b
LEFT JOIN weather_ranked w
ON b.summary_date = w.summary_date
AND b.city = w.city
AND b.country = w.country
AND w.rn = 1
GROUP BY b.summary_date, b.city, b.country;

CREATE OR REPLACE VIEW `project-bad2bf27-d410-468a-acf.weather_mart.v_latest_city_weather` AS
SELECT *
FROM `project-bad2bf27-d410-468a-acf.weather_mart.gold_daily_city_summary`
QUALIFY ROW_NUMBER() OVER (PARTITION BY city ORDER BY summary_date DESC) = 1;

SELECT *
FROM `project-bad2bf27-d410-468a-acf.weather_mart.gold_daily_city_summary`
ORDER BY summary_date DESC, city
LIMIT 20;