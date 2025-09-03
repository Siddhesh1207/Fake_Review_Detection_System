from flask import Flask, request, jsonify
from flask_cors import CORS 
import torch
import pandas as pd
from werkzeug.utils import secure_filename
import os
import torch.nn.functional as F
from transformers import RobertaTokenizer, RobertaForSequenceClassification
from scraper import scrape_booking_reviews 

app = Flask(__name__)
# Configure CORS to allow cross-origin requests
CORS(app) 

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

# --- 4. Define the API Endpoints ---
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
    
@app.route('/scrape-and-predict', methods=['POST'])
def handle_scraping():
    # Check if the request contains a URL
    if not request.json or 'url' not in request.json:
        return jsonify({'error': 'Invalid request. Please provide a "url" key.'}), 400
    
    target_url = request.json['url']
    
    try:
        # Step 1: Call your scraper to get the reviews
        print(f"Starting scrape for URL: {target_url}")
        reviews_df = scrape_booking_reviews(target_url, max_reviews=50)
        
        if reviews_df.empty:
            return jsonify({'error': 'Could not scrape any reviews from the URL.'}), 404

        # Step 2: Loop through the scraped reviews and analyze each one
        results = []
        for review_text in reviews_df['review']:
            # Use your existing prediction function
            prediction, score = predict_review(review_text)
            results.append({
                'review_text': review_text[:100] + "...", # Send a snippet back
                'prediction': prediction.upper(),
                'authenticity_score': f"{score:.2f}"
            })
        
        print("Scraping and analysis complete.")
        # Step 3: Return the full list of results
        return jsonify(results)

    except Exception as e:
        print(f"An error occurred during scraping/analysis: {e}")
        return jsonify({'error': 'An internal error occurred.'}), 500

# NEW: File Analysis Endpoint
@app.route('/analyze-file', methods=['POST'])
def analyze_file():
    print("File analysis request received")
    
    # Check if a file was uploaded
    if 'file' not in request.files:
        print("No file in request.files")
        return jsonify({'error': 'No file provided'}), 400
        
    file = request.files['file']
    print(f"Received file: {file.filename}")
    
    if file.filename == '':
        print("Empty filename")
        return jsonify({'error': 'No file selected'}), 400
        
    if not file.filename.endswith('.csv'):
        print(f"Invalid file type: {file.filename}")
        return jsonify({'error': 'File must be a CSV'}), 400

    try:
        print("Processing file upload")
        # Read the CSV file directly from the request stream
        df = pd.read_csv(file)
        
        if 'review' not in df.columns:
            print("No 'review' column found")
            return jsonify({'error': 'CSV must contain a "review" column'}), 400

        results = []
        # Process each review in the DataFrame
        for review in df['review'].fillna(''):  # Handle any missing values
            if isinstance(review, str) and review.strip():  # Process only non-empty string reviews
                prediction, score = predict_review(review)
                results.append({
                    'review': review,
                    'prediction': prediction.upper(),
                    'authenticity_score': f"{score:.2f}"
                })
        
        return jsonify(results)

    except Exception as e:
        print(f"Error processing file: {e}")
        return jsonify({'error': str(e)}), 500

# --- 5. Run the Flask App ---
if __name__ == '__main__':
    # The app will run on http://127.0.0.1:5000
    app.run(port=5000, debug=True)