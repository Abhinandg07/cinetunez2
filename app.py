from flask import Flask, request, jsonify
import spacy
import requests
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Initialize Flask app
app = Flask(__name__)

# Load spaCy's English language model
nlp = spacy.load("en_core_web_sm")

# Replace with your TMDB API key
TMDB_API_KEY = "c4806ab642cc39cacdf6f2af37808653"

# Replace with your Spotify API credentials (if using Spotify API)
SPOTIFY_CLIENT_ID = "46ea7cc6976c440ca6541c37ec8a7975"
SPOTIFY_CLIENT_SECRET = "7110b1a1e52a4e1fae6d583ea5a0ea71"

def extract_preferences(user_input):
    """
    Extracts user preferences (genres) from the input text using NLP.
    Filters out irrelevant words like "movies" or "music".
    """
    doc = nlp(user_input)
    preferences = set()
    irrelevant_words = {"movies", "movie", "music", "songs", "song"}  # Words to exclude
    for token in doc:
        if token.pos_ in ["NOUN", "ADJ"] and token.text.lower() not in irrelevant_words:
            preferences.add(token.text.lower())
    return list(preferences)

def get_movie_recommendations(genre):
    """
    Fetches movie recommendations from the TMDB API based on a genre.
    """
    genre_map = {
        "action": 28, "comedy": 35, "romance": 10749, "thriller": 53,
        "drama": 18, "horror": 27, "sci-fi": 878, "adventure": 12
    }
    genre_id = genre_map.get(genre.lower(), None)
    if not genre_id:
        return [f"Sorry, I couldn't find movies for the genre '{genre}'."]
    
    # Build the request URL
    url = f"https://api.themoviedb.org/3/discover/movie?api_key={TMDB_API_KEY}&with_genres={genre_id}"
    response = requests.get(url)
    
    # Handle API errors
    if response.status_code != 200:
        return [f"Error: Received status code {response.status_code} from the API."]
    
    data = response.json()
    if 'results' not in data:
        return ["Error: 'results' key not found in the API response."]
    
    return [movie['title'] for movie in data['results'][:5]]

def get_music_recommendations(genre):
    """
    Fetches music recommendations from the Spotify API based on a genre.
    """
    # Authenticate with Spotify API
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET
    ))
    
    # Search for tracks in the specified genre
    results = sp.search(q=f"genre:{genre}", type="track", limit=5)
    tracks = results['tracks']['items']
    
    # Extract track names
    return [track['name'] for track in tracks]

def detect_intent(user_input):
    """
    Detects whether the user wants music or movie recommendations.
    """
    doc = nlp(user_input)
    if "music" in user_input.lower():
        return "music"
    elif "movie" in user_input.lower() or "film" in user_input.lower():
        return "movie"
    else:
        return None

@app.route("/chat", methods=["POST"])
def chat():
    """
    Handles user input and returns recommendations based on intent.
    """
    user_input = request.json.get("message")
    if not user_input:
        return jsonify({"response": "Please provide a message."})
    
    # Detect user intent (music or movies)
    intent = detect_intent(user_input)
    
    if intent == "movie":
        # Extract preferences for movies
        preferences = extract_preferences(user_input)
        if not preferences:
            return jsonify({"response": "I couldn't detect any preferences. Can you tell me more about the type of movies you like?"})
        
        # Fetch movie recommendations
        recommendations = {}
        for genre in preferences:
            recommendations[genre] = get_movie_recommendations(genre)
        
        return jsonify({"response": "Here are some movie recommendations:", "recommendations": recommendations})
    
    elif intent == "music":
        # Extract preferences for music
        preferences = extract_preferences(user_input)
        if not preferences:
            return jsonify({"response": "I couldn't detect any preferences. Can you tell me more about the type of music you like?"})
        
        # Fetch music recommendations
        recommendations = {}
        for genre in preferences:
            recommendations[genre] = get_music_recommendations(genre)
        
        return jsonify({"response": "Here are some music recommendations:", "recommendations": recommendations})
    
    else:
        return jsonify({"response": "I'm not sure what you're asking for. Please specify if you want music or movie recommendations."})
