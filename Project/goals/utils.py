"""Utilities for fetching external exercise data."""
import requests

def get_exercise_video(exercise_name):
    """
    Fetch the video or gif URL for a given exercise from the ExerciseDB API.

    Args:
        exercise_name (str): The slug or name of the exercise to look up.

    Returns:
        str or None: The URL of the exercise gif or video, or None if not found or on error.
    """
    url = f"https://exercisedb.p.rapidapi.com/exercise/{exercise_name}"
    headers = {
        "X-RapidAPI-Host": "exercisedb.p.rapidapi.com",
        "x-rapidapi-key": "215e98e4bamsh44a0ddd9d91062cp107adajsn98198784801e"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException:
        # Log or handle the exception as needed
        return None

    data = response.json()
    if isinstance(data, list) and data:
        return data[0].get('gif_url', '')
    return None
