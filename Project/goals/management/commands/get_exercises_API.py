"""Command-line utility to fetch exercises by name from the ExerciseDB API."""
# pylint: disable=invalid-name

import http.client
import json
import time
import urllib.parse


def main():
    """
    Load exercise names from a file, query the ExerciseDB API,
    and save matched exercises to a JSON file.
    """
    try:
        with open("accessible_exercise_names.txt", "r", encoding="utf-8") as f:
            exercise_names = [line.strip() for line in f if line.strip()]
    except OSError as e:
        print(f"Error reading input file: {e}")
        return

    conn = http.client.HTTPSConnection("exercisedb.p.rapidapi.com")
    headers = {
        "x-rapidapi-host": "exercisedb.p.rapidapi.com",
        "x-rapidapi-key": "584fb71dc8msh70a768bec023ee2p1deb47jsna5aa2d4e703b",
    }

    matched = []

    for name in exercise_names:
        encoded_name = urllib.parse.quote(name.lower())
        endpoint_path = f"/exercises/name/{encoded_name}?offset=0&limit=1"
        try:
            conn.request("GET", endpoint_path, headers=headers)
            res = conn.getresponse()
            data = res.read()
            result = json.loads(data.decode("utf-8"))
        except (http.client.HTTPException, json.JSONDecodeError) as e:
            print(f"Error fetching {name}: {e}")
            continue

        if isinstance(result, list) and result:
            matched.append(result[0])
            print(f"✓ Found: {name}")
        else:
            print(f"✗ Not found: {name}")

        time.sleep(0.3)

    try:
        with open("final_accessible_exercises.json", "w", encoding="utf-8") as f:
            json.dump(matched, f, indent=4)
    except OSError as e:
        print(f"Error writing output file: {e}")
        return

    print(f"\nFinished! Saved {len(matched)} matched exercises.")


if __name__ == "__main__":
    main()
