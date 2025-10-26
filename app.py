from flask import Flask, render_template, request, jsonify, send_from_directory
import pickle
import json
import numpy as np
from tensorflow.keras.models import load_model
from nltk.stem import WordNetLemmatizer
import nltk
import random
from fuzzywuzzy import fuzz, process
import re

# -------------------- NLTK Setup --------------------
nltk.download('punkt')
nltk.download('wordnet')

lemmatizer = WordNetLemmatizer()

# -------------------- Flask Config --------------------
app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable cache for dev

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory('assets', filename)

# -------------------- Load Model and Data --------------------
try:
    model = load_model('model/chatbot_model.h5')

    with open('intents.json', 'r', encoding='utf-8') as file:
        intents = json.load(file)

    words = pickle.load(open('model/words.pkl', 'rb'))
    classes = pickle.load(open('model/classes.pkl', 'rb'))

except Exception as e:
    print("⚠️ Error loading model or data:", e)
    raise SystemExit("Essential files missing, exiting.")

# -------------------- Whitelist for Codec-related topics --------------------
ALLOWED_TAGS = [
    "greeting",
    "about",
    "founder",
    "mission",
    "services",
    "internship",
    "internship_process",
    "technologies_used",
    "projects",
    "project_support",
    "team",
    "achievements",
    "help",
    "contact",
    "contact_info",
    "location",
    "thanks",
    "goodbye",
    "how_are_you",
    "capabilities",
    "identity",
    "creator",
    # moderation / safety intents (allow so the bot can reply professionally)
    "insult",
    "inappropriate",
    # out-of-scope / fallback handlers (handled specially in code)
    "random_questions",
    "fallback",
    # UX helper intents
    "single_letter"
]

# Short regex-based out-of-scope detector (sports / movies / celebrity / trivial topics)
OUT_OF_SCOPE_KEYWORDS = [
    # sports & players
    "cricket", "football", "soccer", "match", "score", "innings", "t20", "odi", "test",
    "dhoni", "virat", "kohli", "rohit", "sachin", "smith", "babar", "root", "kane",
    "nba", "ipl", "icc", "fifa",
    # movies & celebrities
    "movie", "film", "actor", "actress", "box office", "oscar", "oscars", "grossing",
    "celebrity", "celebs", "cast", "director", "trailer",
    # generic trivia / social chatter
    "joke", "meme", "viral", "who will win", "who won", "vs", "versus"
]

# compile once as word-boundary regex (escape keywords)
OUT_OF_SCOPE_RE = re.compile(r"\b(?:" + "|".join(re.escape(k) for k in OUT_OF_SCOPE_KEYWORDS) + r")\b", re.IGNORECASE)

def is_out_of_scope(query: str) -> bool:
    """Return True when query clearly references sports/movies/celebrity/trivia."""
    if not query:
        return False
    return bool(OUT_OF_SCOPE_RE.search(query))

# -------------------- Helper Functions --------------------
def clean_up_sentence(sentence):
    sentence_words = nltk.word_tokenize(sentence)
    return [lemmatizer.lemmatize(word.lower()) for word in sentence_words]

def bag_of_words(sentence):
    sentence_words = clean_up_sentence(sentence)
    bag = [0] * len(words)
    for s in sentence_words:
        for i, w in enumerate(words):
            if w == s:
                bag[i] = 1
    return np.array(bag)

def correct_spelling(sentence: str) -> str:
    """
    Safer spelling correction:
    - Do per-word fuzzy correction using words that appear in intent patterns.
    - Only replace when the fuzzy match is very strong and lengths are similar.
    - Avoid replacing the whole sentence with a single pattern.
    """
    try:
        tokenized = nltk.word_tokenize(sentence.lower())
    except Exception:
        return sentence

    # collect candidate words from all intent patterns (lowercased, unique)
    pattern_words = set()
    for intent in intents.get('intents', []):
        for p in intent.get('patterns', []):
            for w in nltk.word_tokenize(p.lower()):
                if w.isalpha():
                    pattern_words.add(w)

    pattern_words = list(pattern_words)
    if not pattern_words:
        return sentence

    corrected_tokens = []
    for tok in tokenized:
        # don't attempt to correct very short tokens or non-alpha tokens
        if not tok.isalpha() or len(tok) <= 2:
            corrected_tokens.append(tok)
            continue

        best = process.extractOne(tok, pattern_words, scorer=fuzz.ratio)
        # require a high score and not-too-different length to accept correction
        if best and best[1] >= 85 and abs(len(best[0]) - len(tok)) <= 2:
            corrected_tokens.append(best[0])
        else:
            corrected_tokens.append(tok)

    corrected_sentence = " ".join(corrected_tokens)
    # debug: only print if we actually changed something
    if corrected_sentence != sentence.lower():
        print(f"🔤 Corrected input '{sentence}' → '{corrected_sentence}'")
    return corrected_sentence

def find_closest_pattern(sentence: str):
    """Find closest pattern to handle fuzzy fallbacks with stricter checks."""
    all_patterns = []
    pattern_to_tag = {}
    for intent in intents['intents']:
        for pattern in intent.get('patterns', []):
            all_patterns.append(pattern)
            pattern_to_tag[pattern] = intent.get('tag')

    if not all_patterns:
        return None

    best_match = process.extractOne(sentence, all_patterns, scorer=fuzz.token_set_ratio)
    # require a reasonably high score and ensure target intent has responses
    if best_match and best_match[1] >= 75:
        candidate = pattern_to_tag.get(best_match[0])
        intent_obj = next((it for it in intents['intents'] if it.get('tag') == candidate), None)
        if intent_obj and intent_obj.get('responses'):
            print(f"🔎 Fuzzy fallback matched '{sentence}' -> pattern '{best_match[0]}' (score {best_match[1]}) -> tag '{candidate}'")
            return candidate
    return None

def predict_class(sentence):
    """Predict the intent class for the user input sentence."""
    corrected_sentence = correct_spelling(sentence)
    bow = bag_of_words(corrected_sentence)
    res = model.predict(np.array([bow]))[0]
    
    # Debug print
    print(f"\nDEBUG - Input: {sentence}")
    print(f"Corrected: {corrected_sentence}")
    print(f"Top 3 predictions:")
    top_3 = sorted(enumerate(res), key=lambda x: x[1], reverse=True)[:3]
    for idx, prob in top_3:
        if idx < len(classes):
            print(f"- {classes[idx]}: {prob:.4f}")

    ERROR_THRESHOLD = 0.1
    results = [[i, r] for i, r in enumerate(res) if r > ERROR_THRESHOLD]
    results.sort(key=lambda x: x[1], reverse=True)
    
    return_list = []
    for r in results:
        if r[0] < len(classes):  # Ensure index is valid
            return_list.append({
                "intent": classes[r[0]], 
                "probability": str(r[1])
            })

    # Prevent 'single_letter' intent from being returned for non single-letter inputs
    if not is_single_letter(sentence):
        return_list = [r for r in return_list if r['intent'] != 'single_letter']

    # If no model results, try fuzzy fallback but avoid mapping non-letter inputs to 'single_letter'
    if not return_list:
        closest = find_closest_pattern(sentence)
        if closest and not (closest == 'single_letter' and not is_single_letter(sentence)):
            return_list = [{"intent": closest, "probability": "0.7"}]

    return return_list

def get_response(intents_list, intents_json):
    """
    Return a response from intents.json.
    - If model returned an intent and that intent has responses -> return one.
    - Otherwise return the 'fallback' intent response from intents.json (if present).
    """
    # 1) No prediction -> fallback
    if not intents_list:
        fallback_intent = next((it for it in intents_json.get('intents', []) if it.get('tag') == 'fallback'), None)
        if fallback_intent and fallback_intent.get('responses'):
            return random.choice(fallback_intent['responses'])
        return "I'm not trained to answer that. Please ask about Codec Technologies."

    # 2) Predicted tag -> return its response if available
    tag = intents_list[0].get('intent')
    intent_obj = next((it for it in intents_json.get('intents', []) if it.get('tag') == tag), None)
    if intent_obj and intent_obj.get('responses'):
        return random.choice(intent_obj['responses'])

    # 3) Predicted tag missing/has no responses -> fallback
    fallback_intent = next((it for it in intents_json.get('intents', []) if it.get('tag') == 'fallback'), None)
    if fallback_intent and fallback_intent.get('responses'):
        return random.choice(fallback_intent['responses'])

    # 4) Ultimate fallback
    return "I'm not trained to answer that. Please ask about Codec Technologies."

def is_single_letter(s: str) -> bool:
    """Return True only for a single alphabetical character (no digits/punctuation)."""
    if not s:
        return False
    s = s.strip()
    return len(s) == 1 and s.isalpha()

# -------------------- Routes --------------------
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get', methods=['POST'])
def chatbot_response():
    try:
        data = request.get_json(force=True)
        user_message = (data.get('message') or data.get('msg') or '').strip()
        if not user_message:
            return jsonify({'response': "Please type something first!"})

        # 1) Single-letter guard (existing)
        if is_single_letter(user_message):
            for intent in intents.get('intents', []):
                if intent.get('tag') == 'single_letter' and intent.get('responses'):
                    return jsonify({'response': random.choice(intent['responses'])})

        # 2) NEW: regex out-of-scope check -> immediate random_questions/fallback response
        if is_out_of_scope(user_message):
            rand_intent = next((it for it in intents.get('intents', []) if it.get('tag') == 'random_questions'), None)
            if rand_intent and rand_intent.get('responses'):
                return jsonify({'response': random.choice(rand_intent['responses'])})
            fallback_int = next((it for it in intents.get('intents', []) if it.get('tag') == 'fallback'), None)
            if fallback_int and fallback_int.get('responses'):
                return jsonify({'response': random.choice(fallback_int['responses'])})
            return jsonify({'response': "That's outside my domain 😅 but I can help with Codec Technologies related queries."})

        # 3) Normal ML/fuzzy flow
        intents_detected = predict_class(user_message)
        bot_reply = get_response(intents_detected, intents)
        return jsonify({'response': bot_reply})

    except Exception as e:
        print("❌ Error:", e)
        return jsonify({'response': "Oops! Something went wrong."})

# -------------------- Run --------------------
if __name__ == '__main__':
    print("🚀 Codec AI Chatbot is running at http://127.0.0.1:5000")
    app.run(debug=True)
