from flask import Flask, request, jsonify
from flask_cors import CORS 
import torch

app = Flask(__name__)
CORS(app) 

import torch.nn.functional as F
from transformers import RobertaTokenizer, RobertaForSequenceClassification

# --- 2. Load the Saved Model and Tokenizer ---
# This part is run only once when the app starts
MODEL_PATH = './final_model_distilroberta'
print("Loading the saved model and tokenizer...")
try:
    tokenizer = RobertaTokenizer.from_pretrained(MODEL_PATH)
    model = RobertaForSequenceClassification.from_pretrained(MODEL_PATH)
    model.eval() # Set the model to evaluation mode
    print("Model loaded successfully!")
except Exception as e:
    print(f"Error loading model: {e}")
    # Exit if the model can't be loaded
    exit()

# The LabelEncoder used in training likely mapped 'fake' to 0 and 'real' to 1
LABELS = ['fake', 'real']

# --- 3. Create the Prediction Function ---
def predict_review(review_text):
    """
    This function takes a review text, runs it through the model,
    and returns the prediction and authenticity score.
    """
    # Tokenize the input text
    inputs = tokenizer(review_text, return_tensors="pt", padding=True, truncation=True, max_length=256)

    # Get the model's prediction
    with torch.no_grad():
        outputs = model(**inputs)

    logits = outputs.logits

    # Apply softmax to convert logits to probabilities
    probabilities = F.softmax(logits, dim=1)

    # Get the prediction and the score
    prediction_index = torch.argmax(probabilities, dim=1).item()
    predicted_label = LABELS[prediction_index]
    
    # The authenticity score is the probability of the review being 'real' (class 1)
    authenticity_score = probabilities[0][1].item() * 100

    return predicted_label, authenticity_score

# --- 4. Define the API Endpoint ---
@app.route('/predict', methods=['POST'])
def handle_prediction():
    """
    This is the main API endpoint. It receives a review and returns a prediction.
    """
    if not request.json or 'review' not in request.json:
        return jsonify({'error': 'Invalid request. Please provide a JSON with a "review" key.'}), 400

    review_text = request.json['review']

    try:
        prediction, score = predict_review(review_text)
        
        # Prepare the successful response
        response_data = {
            'prediction': prediction.upper(),
            'authenticity_score': f"{score:.2f}"
        }
        return jsonify(response_data)

    except Exception as e:
        print(f"Error during prediction: {e}")
        return jsonify({'error': 'Failed to process the review.'}), 500

# --- 5. Run the Flask App ---
if __name__ == '__main__':
    # The app will run on http://127.0.0.1:5000
    app.run(port=5000, debug=True)
