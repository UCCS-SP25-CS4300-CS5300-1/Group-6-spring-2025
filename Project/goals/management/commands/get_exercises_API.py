import http.client
import json
import time
import urllib.parse

# Load accessible names
with open("accessible_exercise_names.txt", "r", encoding="utf-8") as f:
    exercise_names = [line.strip() for line in f if line.strip()]

conn = http.client.HTTPSConnection("exercisedb.p.rapidapi.com")

headers = {
    'x-rapidapi-key': "584fb71dc8msh70a768bec023ee2p1deb47jsna5aa2d4e703b",
    'x-rapidapi-host': "exercisedb.p.rapidapi.com"
}

matched = []

for name in exercise_names:
    # Properly URL encode the name
    encoded_name = urllib.parse.quote(name.lower())
    endpoint = f"/exercises/name/{encoded_name}?offset=0&limit=1"

    try:
        conn.request("GET", endpoint, headers=headers)
        res = conn.getresponse()
        data = res.read()

        result = json.loads(data.decode("utf-8"))

        if isinstance(result, list) and result:
            matched.append(result[0])
            print(f"✓ Found: {name}")
        else:
            print(f"✗ Not found: {name}")

    except Exception as e:
        print(f"Error with {name}: {e}")

    # Optional delay to avoid hitting rate limits (tweak as needed)
    time.sleep(0.3)

# Save the results to a JSON file
with open("final_accessible_exercises.json", "w", encoding="utf-8") as f:
    json.dump(matched, f, indent=4)

print(f"\nFinished! Saved {len(matched)} matched exercises.")
