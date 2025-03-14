from flask import Flask, request, jsonify
import spacy
import requests

app = Flask(__name__)
nlp = spacy.load("en_core_web_sm")
TMDB_API_KEY = "c4806ab642cc39cacdf6f2af37808653"

def extract_preferences(user_input):
    doc = nlp(user_input)
    preferences = set()
    for token in doc:
        if token.pos_ in ["NOUN", "ADJ"]:
            preferences.add(token.text.lower())
    return list(preferences)

def get_movie_recommendations(genre):
    genre_map = {
        "action": 28, "comedy": 35, "romance": 10749, "thriller": 53,
        "drama": 18, "horror": 27, "sci-fi": 878, "adventure": 12
    }
    genre_id = genre_map.get(genre.lower(), None)
    if not genre_id:
        return [f"Sorry, I couldn't find movies for the genre '{genre}'."]
    url = f"https://api.themoviedb.org/3/discover/movie?api_key={TMDB_API_KEY}&with_genres={genre_id}"
    response = requests.get(url)
    if response.status_code != 200:
        return [f"Error: Received status code {response.status_code} from the API."]
    data = response.json()
    if 'results' not in data:
        return ["Error: 'results' key not found in the API response."]
    return [movie['title'] for movie in data['results'][:5]]

@app.route("/chat", methods=["POST"])  # Allow POST requests
def chat():
    user_input = request.json.get("message")
    if not user_input:
        return jsonify({"response": "Please provide a message."})
    
    preferences = extract_preferences(user_input)
    if not preferences:
        return jsonify({"response": "I couldn't detect any preferences. Can you tell me more?"})
    
    recommendations = {}
    for genre in preferences:
        recommendations[genre] = get_movie_recommendations(genre)
    
    return jsonify({"response": "Here are some recommendations:", "recommendations": recommendations})

if __name__ == "__main__":
    app.run(debug=True)
