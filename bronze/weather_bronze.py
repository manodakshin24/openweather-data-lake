import os
import json
import requests
from datetime import datetime, timezone
from google.cloud import storage

# --- CONFIG ---
API_KEY = os.getenv("OPENWEATHER_API_KEY")
BUCKET_NAME = "weather-data-dakshin-2026"  # change this
CITIES = ["Hartford", "New York", "Boston", "London", "Tokyo", "Amsterdam", "Madrid", 
          "Paris", "Vancouver", "Florence", "Detroit", "Austin", "Tampa", "Orlando", "Key West",
          "Miami", "Chicago", "Seattle", "Denver", "Phoenix", "Cleveland", "Boulder", "Tucson",
          "Dallas", "San Francisco", "Los Angeles", "San Diego", "Berlin", "Beijing"]

BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

storage_client = storage.Client()
bucket = storage_client.bucket(BUCKET_NAME)

def fetch_weather(city):
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "imperial"  # use "metric" if you prefer Celsius
    }
    response = requests.get(BASE_URL, params=params, timeout=30)

    if response.status_code != 200:
        print(f"Error fetching {city}: {response.text}")
        return None

    return response.json()


def upload_to_gcs(city, data):
    now = datetime.now(timezone.utc)

    year = now.strftime("%Y")
    month = now.strftime("%m")
    day = now.strftime("%d")
    timestamp = now.strftime("%Y%m%dT%H%M%SZ")

    city_clean = city.lower().replace(" ", "_")

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
        print(f"Fetching weather for {city}...")
        data = fetch_weather(city)

        if data:
            upload_to_gcs(city, data)


if __name__ == "__main__":
    main()