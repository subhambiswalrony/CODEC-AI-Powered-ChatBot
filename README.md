# 🤖 Codec AI Assistant

![Codec Logo](assets/logo-removebg-preview.png)

A smart AI-powered chatbot built with Python, Flask, and TensorFlow that provides information about Codec Technologies, its services, internships, and more.

## ✨ Features

- **Natural Language Understanding** 🧠: Understands user queries using NLP techniques
- **Intent Recognition** 🎯: Identifies user intent to provide relevant responses
- **Typo Tolerance** ✍️: Handles spelling mistakes and typos in user queries
- **Responsive UI** 💻: Clean and user-friendly chat interface
- **Real-time Interaction** ⚡: Instant responses to user queries

## 📁 Project Structure

```
├── app.py                  # Flask application main file
├── assets/                 # Images and other static assets
├── chatbot_model.py        # Neural network model definition
├── pyrightconfig.json      # silence all import warnings across entire workspace
├── intents.json            # Training data with intents and responses
├── model/                  # Trained model files
│   ├── chatbot_model.h5    # Keras model
│   ├── classes.pkl         # Intent classes
│   └── words.pkl           # Vocabulary
├── nltk_download_fix.py    # Helper for NLTK resources
├── static/                 # CSS and JavaScript files
│   ├── style.css           # Styling
│   └── script.js           # Frontend logic
│   templates/              # HTML templates
│   └── index.html          # Chat UI
└── README.md               # Project documentation
```

## Prerequisites 🧰
- Python 3.8+  
- pip packages:
  - flask, tensorflow (or tensorflow-cpu), nltk, fuzzywuzzy, python-Levenshtein, numpy

Install:
```bash
pip install flask tensorflow nltk fuzzywuzzy python-Levenshtein numpy
```

## 🚀 Installation

1. Clone the repository or download the source code

2. Install the required dependencies:
   ```
   pip install flask tensorflow nltk python-Levenshtein fuzzywuzzy
   ```

3. Download required NLTK resources:
   ```
   python nltk_download_fix.py
   ```

4. Run the application:
   ```
   python app.py
   ```

5. Open your browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```

## 🎓 Training the Model

1. Prepare your training data:
   - Open `intents.json`
   - Add your custom intents in the following format:
   ```json
   {
     "intents": [
       {
         "tag": "greeting",
         "patterns": ["Hi", "Hello", "Hey there"],
         "responses": ["Hello!", "Hi there!", "Greetings!"]
       }
     ]
   }
   ```

2. Train the model:
   ```
   python chatbot_model.py
   ```
   This will:
   - Process the intents.json file
   - Create word embeddings
   - Train the neural network
   - Save the model and required files in the `model/` directory

3. Monitor training:
   - Watch the training progress and accuracy
   - Model will be saved automatically when training completes
   - Check the console output for any errors or warnings

4. Verify the trained model:
   - Ensure all files are generated in the `model/` directory
   - Test the chatbot with new queries
   - Fine-tune the model if needed by adjusting parameters in `chatbot_model.py`

## ⚙️ How It Works

1. The chatbot uses a neural network trained on predefined intents in `intents.json`
2. User messages are processed using natural language techniques:
   - 📝 Tokenization
   - 🔄 Lemmatization
   - 📊 Bag-of-words representation
3. The model predicts the most likely intent for the user's query
4. A response is selected from the matched intent's response list
5. For factual questions outside the bot's knowledge domain, it provides a helpful message directing users to appropriate resources

## 🛠️ Customization

To customize the chatbot for your needs:

1. Modify the `intents.json` file to include your own intents and responses
2. Run `chatbot_model.py` to retrain the model with your data
3. Adjust the UI in `templates/index.html` and `static/style.css` as needed

## Intents & Safety ⚖️
- Keep Codec-only topics in `intents.json`. Use `random_questions` or `fallback` tags for off-topic patterns.  
- Add `inappropriate` / `insult` intents (already present) for quick detection and responses.  
- Retrain model after editing `intents.json`.

## Troubleshooting 🛠️
- Bot answering wrong tag? Check `model/classes.pkl` order matches `intents.json` tags — retrain if mismatched.  
- Overly aggressive filters? Adjust `is_inappropriate()` and keyword lists in `app.py`.  
- No response for new intents? Re-run `chatbot_model.py` and restart `app.py`.

## Quick tips ✅
- Add polite responses for insults/off-topic in `intents.json` rather than relying only on code-level filters.  
- Log rejected queries (`rejected_queries.log`) for tuning deny lists.  

## 💻 Technologies Used

- **Flask** 🌶️: Web framework
- **TensorFlow/Keras** 🧠: Neural network implementation
- **NLTK** 📚: Natural language processing
- **FuzzyWuzzy** 🔍: String matching and typo tolerance
- **HTML/CSS/JavaScript** 🎨: Frontend interface

## 📄 License

This project is created for educational purposes as part of Codec Technologies' training program.

## 🙏 Credits

Developed as part of the AI project at Codec Technologies.
Developed by Subham Biswal ❤️.
