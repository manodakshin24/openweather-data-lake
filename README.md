# OpenWeather Data Lake Using the Medallion Architecture (Bronze -> Silver -> Gold)

A weather analytics pipeline using the OpenWeather API, Google Cloud Storage (GCS), and BigQuery.

This project demonstrates how to build a data lake using the Medallion Architecture with data fetched from the OpenWeather API, Google Cloud Storage (GCS), and BigQuery. The Medallion Architecture consists of three layers: Bronze, Silver, and Gold. Each layer serves a specific purpose in the data processing pipeline. It serves as a proof of concept of what I learned from the Udemy course "Data Engineer Foundations: Build Modern Data Systems".

## What This Project Does
- Ingests live weather JSON data for multiple cities from OpenWeather (Bronze layer)
- Transforms raw JSON into Parquet records (Silver layer)
- Builds daily city-level summary tables and views in BigQuery (Gold layer)

## Pipeline Layers

- Bronze: JSON files of raw data, stored in GCS
  Source script: [bronze/weather_bronze.py](bronze/weather_bronze.py)
- Silver: Parquet files of transformed data, stored in GCS
  Source script: [silver/weather_silver.py](silver/weather_silver.py)
- Gold: BigQuery schemas, summary table, and view for analytics
  SQL script: [gold/weather_gold.sql](gold/weather_gold.sql)

## Project Structure

- [bronze/weather_bronze.py](bronze/weather_bronze.py): Fetches weather data and uploads JSON to GCS
- [silver/weather_silver.py](silver/weather_silver.py): Reads Bronze JSON from GCS, transforms, writes Parquet to GCS
- [gold/weather_gold.sql](gold/weather_gold.sql): Creates BigQuery data model and aggregations
- [requirements.txt](requirements.txt): Python dependencies

## Prerequisites
- Python 3.10+
- Google Cloud project with:
  - Cloud Storage bucket
  - BigQuery enabled
  - Service account credentials configured locally
- OpenWeather API key

## Installation

```bash
python3 -m venv virtualEnv
source virtualEnv/bin/activate
pip install -r requirements.txt
```

Configuration
Create a local .env file (do not commit it):
OPENWEATHER_API_KEY=[insert_your_openweather_api_key_here]
WEATHER_BUCKET=weather-data-dakshin-2026

Current scripts use:

OPENWEATHER_API_KEY for API access
WEATHER_BUCKET in Silver
BUCKET_NAME constant in Bronze (can be changed to use env for consistency)
If needed, export vars manually:

export OPENWEATHER_API_KEY="your_openweather_api_key"
export WEATHER_BUCKET="weather-data-dakshin-2026"

Run the Pipeline
1. Bronze ingestion (API -> GCS JSON)
python bronze/weather_bronze.py

2. Silver transformation (GCS JSON -> GCS Parquet)
python silver/weather_silver.py

Gold modeling in BigQuery
Run weather_gold.sql in BigQuery Console (or bq query) to create:

- weather_lake schema
- weather_mart schema
- external Silver table
- daily Gold summary table
- latest-city weather view

## Security Note
- Do not commit .env or service account key files.
- Rotate keys immediately if exposed.

## GCS Path Layout
- Bronze: bronze/city=<city>/year=<YYYY>/month=<MM>/day=<DD>/<timestamp>.json
- Silver: silver/city=<city>/year=<YYYY>/month=<MM>/day=<DD>/<timestamp>.parquet
