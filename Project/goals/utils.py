import requests
from django.conf import settings

# Fetch exercises and video/gif links from ExerciseDB API
def get_exercise_video(exercise_name):
    url = f"https://exercisedb.p.rapidapi.com/exercise/{exercise_name}"
    
    headers = {
        "X-RapidAPI-Host": "exercisedb.p.rapidapi.com",
        "x-rapidapi-key": "215e98e4bamsh44a0ddd9d91062cp107adajsn98198784801e"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        if data:
            # Example: Return video or gif if available
            return data[0].get('gif_url', '')  # You may need to adjust based on the data structure
    return None
