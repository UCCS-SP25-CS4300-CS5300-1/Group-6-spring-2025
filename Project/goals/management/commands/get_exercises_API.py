import http.client
import json
import time
import urllib.parse
import requests
import os

# Load accessible names
with open("accessible_exercise_names.txt", "r", encoding="utf-8") as f:
    exercise_names = [line.strip() for line in f if line.strip()]

conn = http.client.HTTPSConnection("exercisedb.p.rapidapi.com")

headers = {
    'x-rapidapi-key': "584fb71dc8msh70a768bec023ee2p1deb47jsna5aa2d4e703b",
    'x-rapidapi-host': "exercisedb.p.rapidapi.com"
}

# Load existing data if the file exists
json_path = "final_accessible_exercises.json"
if os.path.exists(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        existing_data = json.load(f)
else:
    existing_data = []

# Create a dictionary for quick lookup by name (case-insensitive)
existing_data_dict = {entry['name'].lower(): entry for entry in existing_data}

updated_data = []

for name in exercise_names:
    encoded_name = urllib.parse.quote(name.lower())
    endpoint = f"/exercises/name/{encoded_name}?offset=0&limit=1"

    try:
        conn.request("GET", endpoint, headers=headers)
        res = conn.getresponse()
        data = res.read()
        result = json.loads(data.decode("utf-8"))

        if isinstance(result, list) and result:
            new_entry = result[0]
            updated_data.append(new_entry)
            existing_data_dict[name.lower()] = new_entry  # Replace or insert
            print(f"✓ Updated: {name}")
        else:
            print(f"✗ Not found: {name}")

    except Exception as e:
        print(f"Error with {name}: {e}")

    time.sleep(0.3)  # To respect rate limits

# Convert updated dictionary back to list for saving
final_data = list(existing_data_dict.values())

with open(json_path, "w", encoding="utf-8") as f:
    json.dump(final_data, f, indent=4)

print(f"\nFinished! Saved {len(final_data)} total matched exercises.")
