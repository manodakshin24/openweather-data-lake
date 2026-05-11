import os
import json
import time
import requests
from datetime import datetime, timezone
from google.cloud import storage

# --- CONFIG ---
API_KEY = os.getenv("OPENWEATHER_API_KEY")
BUCKET_NAME = "weather-data-dakshin-2026"

CITIES = ["Hartford", "New York", "Boston", "London", "Tokyo", "Amsterdam", "Madrid", 
          "Paris", "Vancouver", "Florence", "Detroit", "Austin", "Tampa", "Orlando", "Key West",
          "Miami", "Chicago", "Seattle", "Denver", "Phoenix", "Cleveland", "Boulder", "Tucson",
          "Dallas", "San Francisco", "Los Angeles", "San Diego", "Berlin", "Beijing", "Shanghai",
          "Bangkok", "San Jose", "Cambridge", "Milan", "Philadelphia", "Pittsburgh"]

FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"


storage_client = storage.Client()
bucket = storage_client.bucket(BUCKET_NAME)

def fetch_forecast(city):
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "imperial"  # use "metric" for Celsius
    }
    r = requests.get(FORECAST_URL, params=params, timeout=30)
    if r.status_code != 200:
        print(f"Forecast fetch failed for {city}: {r.text}")
        return None
    return r.json()


def upload_to_gcs(city, data):
    now = datetime.now(timezone.utc)
    city_clean = city.lower().replace(" ", "_")

    year = now.strftime("%Y")
    month = now.strftime("%m")
    day = now.strftime("%d")
    timestamp = now.strftime("%Y%m%dT%H%M%SZ")

    blob_path = (
        f"bronze/city={city_clean}/"
        f"year={year}/month={month}/day={day}/"
        f"{timestamp}.json"
    )

    blob = bucket.blob(blob_path)
    blob.upload_from_string(
        data=json.dumps(data),
        content_type="application/json"
    )

    print(f"Uploaded: gs://{BUCKET_NAME}/{blob_path}")


def main():
    if not API_KEY:
        raise ValueError("OPENWEATHER_API_KEY not set")

    for city in CITIES:
        print(f"Fetching 5-day forecast for {city}...")
        data = fetch_forecast(city)
        if data:
            upload_to_gcs(city, data)
        time.sleep(0.2)  # reduce rate-limit risk

if __name__ == "__main__":
    main()