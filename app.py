from flask import Flask, render_template, request, jsonify
import pickle
import json
import numpy as np
from tensorflow.keras.models import load_model
from nltk.stem import WordNetLemmatizer
import nltk
import random
from fuzzywuzzy import fuzz, process

# -------------------- NLTK Setup --------------------
nltk.download('punkt')
nltk.download('wordnet')

lemmatizer = WordNetLemmatizer()

# -------------------- Flask App Config --------------------
app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching for development

# Configure assets folder for serving images
from flask import send_from_directory

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory('assets', filename)

# -------------------- Load Model and Data --------------------
try:
    model = load_model('model/chatbot_model.h5')

    # ✅ FIX: Read intents.json safely with UTF-8 encoding
    with open('intents.json', 'r', encoding='utf-8') as file:
        intents = json.load(file)

    words = pickle.load(open('model/words.pkl', 'rb'))
    classes = pickle.load(open('model/classes.pkl', 'rb'))

except Exception as e:
    print("⚠️ Error loading model or data:", e)
    raise SystemExit("Exiting because essential files could not be loaded.")


# -------------------- Helper Functions --------------------
def clean_up_sentence(sentence: str):
    """Tokenize and lemmatize the user input sentence."""
    sentence_words = nltk.word_tokenize(sentence)
    sentence_words = [lemmatizer.lemmatize(word.lower()) for word in sentence_words]
    return sentence_words


def bag_of_words(sentence: str):
    """Convert a sentence into a bag-of-words numpy array."""
    sentence_words = clean_up_sentence(sentence)
    bag = [0] * len(words)
    for s in sentence_words:
        for i, w in enumerate(words):
            if w == s:
                bag[i] = 1
    return np.array(bag)


def correct_spelling(sentence: str):
    """Attempt to correct spelling mistakes in the input sentence using patterns from intents."""
    # Extract all patterns from intents for matching
    all_patterns = []
    for intent in intents['intents']:
        all_patterns.extend(intent['patterns'])
    
    # Tokenize the input sentence
    words = nltk.word_tokenize(sentence.lower())
    corrected_words = []
    
    for word in words:
        # Skip very short words (like "a", "I", etc.)
        if len(word) <= 2:
            corrected_words.append(word)
            continue
            
        # Find the best match for each word from all words in patterns
        pattern_words = []
        for pattern in all_patterns:
            pattern_words.extend([w.lower() for w in nltk.word_tokenize(pattern)])
        
        # Remove duplicates
        pattern_words = list(set(pattern_words))
        
        # Find the best match
        if pattern_words:
            best_match = process.extractOne(word, pattern_words, scorer=fuzz.ratio)
            # Only correct if the match is reasonably good (score > 70)
            if best_match and best_match[1] > 70:
                corrected_words.append(best_match[0])
            else:
                corrected_words.append(word)
        else:
            corrected_words.append(word)
    
    return " ".join(corrected_words)

def find_closest_pattern(sentence: str):
    """Find the closest matching pattern from intents."""
    all_patterns = []
    pattern_to_tag = {}
    
    # Extract all patterns and map them to their tags
    for intent in intents['intents']:
        for pattern in intent['patterns']:
            all_patterns.append(pattern)
            pattern_to_tag[pattern] = intent['tag']
    
    # Find the best match
    best_match = process.extractOne(sentence, all_patterns, scorer=fuzz.token_set_ratio)
    
    if best_match and best_match[1] > 60:  # Threshold for accepting a match
        return pattern_to_tag[best_match[0]]
    
    return None

def predict_class(sentence: str):
    """Predict the intent class for the user input sentence."""
    # First try to correct spelling mistakes
    corrected_sentence = correct_spelling(sentence)
    
    # Use bag of words with the corrected sentence
    bow = bag_of_words(corrected_sentence)
    res = model.predict(np.array([bow]))[0]

    # Set appropriate confidence threshold
    ERROR_THRESHOLD = 0.25
    
    results = [[i, r] for i, r in enumerate(res) if r > ERROR_THRESHOLD]
    
    # If no results above threshold, try fuzzy matching
    if not results:
        closest_tag = find_closest_pattern(sentence)
        if closest_tag:
            # Find the index of the closest tag in classes
            try:
                tag_index = classes.index(closest_tag)
                return [{"intent": closest_tag, "probability": "0.7"}]  # Arbitrary probability
            except ValueError:
                pass
    
    results.sort(key=lambda x: x[1], reverse=True)
    return [{"intent": classes[r[0]], "probability": str(r[1])} for r in results]


def get_response(intents_list, intents_json):
    """Return a suitable response based on predicted intent."""
    if len(intents_list) == 0:
        # ❌ Fallback for irrelevant / low-confidence / non-Codec questions
        return random.choice([
            "I’m not trained to answer that. Try asking me about Codec Technologies 😊",
            "Sorry, I can only help with questions related to Codec Technologies.",
            "That’s outside my scope! Ask me something about Codec internships, services, or training."
        ])

    tag = intents_list[0]['intent']
    for i in intents_json['intents']:
        if i['tag'] == tag:
            return random.choice(i['responses'])

    return "I'm sorry, I couldn't find a suitable answer."


# -------------------- Flask Routes --------------------
@app.route('/')
def home():
    """Render the main chatbot HTML page."""
    return render_template('index.html')


@app.route('/get', methods=['POST'])
def chatbot_response():
    """Handle AJAX requests from the frontend and return chatbot responses."""
    try:
        data = request.get_json(force=True)
        user_message = data.get('message', '').strip()

        if not user_message:
            return jsonify({'response': "Please enter a valid message."})

        intents_detected = predict_class(user_message)
        bot_reply = get_response(intents_detected, intents)

        return jsonify({'response': bot_reply})

    except Exception as e:
        print("❌ Error processing message:", e)
        return jsonify({'response': "Sorry, something went wrong on my end."})


# -------------------- Run Flask App --------------------
if __name__ == '__main__':
    print("🚀 Codec AI Chatbot is running at http://127.0.0.1:5000")
    app.run(debug=True)
