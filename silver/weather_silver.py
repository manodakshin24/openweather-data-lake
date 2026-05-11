import io
import json
import os
from datetime import datetime, timezone

import pandas as pd
from google.cloud import storage

# --- CONFIG ---
BUCKET_NAME = os.getenv("WEATHER_BUCKET", "weather-data-dakshin-2026")

BRONZE_PREFIX = "bronze/"
SILVER_PREFIX = "silver/"

storage_client = storage.Client()
bucket = storage_client.bucket(BUCKET_NAME)

def list_bronze_files():
    # list_blobs handles pagination automatically
    blobs = storage_client.list_blobs(BUCKET_NAME, prefix=BRONZE_PREFIX)
    return [blob.name for blob in blobs if blob.name.endswith(".json")]


def read_json_from_gcs(key):
    blob = bucket.blob(key)
    content = blob.download_as_bytes()
    return json.loads(content)

def extract_city_from_key(key):
    # Expected: bronze/city=hartford/year=.../month=.../day=.../file.json
    parts = key.split("/")
    if len(parts) > 1 and parts[1].startswith("city="):
        return parts[1].split("=", 1)[1]
    return "unknown"

def transform(item, city, country):
    try:
        event_ts = datetime.fromtimestamp(item["dt"], tz=timezone.utc)
        weather_list = item.get("weather", [])
        weather_main = weather_list[0]["main"] if weather_list else None
        weather_desc = weather_list[0].get("description") if weather_list else None

        return {
            "city": city,
            "country": country,
            "temperature": item["main"]["temp"],
            "humidity": item["main"]["humidity"],
            "pressure": item["main"].get("pressure"),
            "wind_speed": item.get("wind", {}).get("speed"),
            "weather": weather_main,
            "weather_description": weather_desc,
            "event_timestamp_utc": event_ts.isoformat(),
            "ingested_at_utc": datetime.now(timezone.utc).isoformat(),
        }
    except KeyError:
        return None

def write_parquet_to_gcs(df, output_blob_name):
    # Write parquet in-memory, then upload to GCS
    buffer = io.BytesIO()
    df.to_parquet(buffer, index=False)
    buffer.seek(0)

    blob = bucket.blob(output_blob_name)
    blob.upload_from_file(buffer, content_type="application/octet-stream")

def process_file(key):
    data = read_json_from_gcs(key)
    city = extract_city_from_key(key)
    country = data.get("city", {}).get("country")

    rows = []
    event_ts_list = []

    for item in data.get("list", []):
        row = transform(item, city, country)
        if row:
            rows.append(row)
            event_ts_list.append(datetime.fromisoformat(row["event_timestamp_utc"]))

    if not rows:
        print(f"Skipping malformed forecast file: {key}")
        return

    df = pd.DataFrame(rows)

    df = df.astype({
        "temperature": "float64",
        "humidity": "float64",
        "pressure": "float64",
        "wind_speed": "float64",
        "city": "string",
        "country": "string",
        "weather": "string",
        "weather_description": "string",
        "event_timestamp_utc": "string",
        "ingested_at_utc": "string",
    })

    latest_ts = max(event_ts_list)
    year = latest_ts.strftime("%Y")
    month = latest_ts.strftime("%m")
    day = latest_ts.strftime("%d")
    ts = latest_ts.strftime("%Y%m%dT%H%M%SZ")

    output_key = (
        f"{SILVER_PREFIX}city={city}/"
        f"year={year}/month={month}/day={day}/"
        f"{ts}.parquet"
    )

    write_parquet_to_gcs(df, output_key)
    print(f"Processed -> gs://{BUCKET_NAME}/{output_key}")


def main():
    files = list_bronze_files()
    print(f"Found {len(files)} bronze files")

    for key in files:
        process_file(key)


if __name__ == "__main__":
    main()