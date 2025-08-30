import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import torch
import torch.nn.functional as F
from transformers import RobertaTokenizer, RobertaForSequenceClassification
from bs4 import BeautifulSoup

# --- 1. Initialize Flask App and CORS ---
app = Flask(__name__)
CORS(app)

# --- 2. Load API Key and ML Model ---
# This part is run only once when the app starts

# Load the secret API key from the environment variable you set on Render
SCRAPINGBEE_API_KEY = os.environ.get('SCRAPINGBEE_API_KEY')
if not SCRAPINGBEE_API_KEY:
    print("FATAL ERROR: SCRAPINGBEE_API_KEY environment variable not set.")
    # In a real app, you might handle this more gracefully, but for now we exit.
    exit()

MODEL_PATH = './final_model_distilroberta'
print("Loading the saved model and tokenizer...")
try:
    tokenizer = RobertaTokenizer.from_pretrained(MODEL_PATH)
    model = RobertaForSequenceClassification.from_pretrained(MODEL_PATH)
    model.eval()
    print("Model loaded successfully!")
except Exception as e:
    print(f"Error loading model: {e}")
    exit()

LABELS = ['fake', 'real']

# --- 3. Prediction Function (No changes here) ---
def predict_review(review_text):
    inputs = tokenizer(review_text, return_tensors="pt", padding=True, truncation=True, max_length=256)
    with torch.no_grad():
        outputs = model(**inputs)
    logits = outputs.logits
    probabilities = F.softmax(logits, dim=1)
    prediction_index = torch.argmax(probabilities, dim=1).item()
    predicted_label = LABELS[prediction_index]
    authenticity_score = probabilities[0][1].item() * 100
    return predicted_label, authenticity_score

# --- 4. NEW: Scraping Function using an API ---
def scrape_with_api(url, max_reviews=50):
    """
    Scrapes reviews for a given Booking.com hotel URL using the ScrapingBee API.
    """
    print("Scraping URL with ScrapingBee API...")
    response = requests.get(
        url='https://app.scrapingbee.com/api/v1/',
        params={
            'api_key': SCRAPINGBEE_API_KEY,
            'url': url,
            'render_js': 'true', # Tell ScrapingBee to run the JavaScript on the page
        },
        timeout=120 # Give the API up to 2 minutes to scrape
    )
    
    if response.status_code != 200:
        print(f"ScrapingBee failed with status code {response.status_code}: {response.text}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    
    scraped_reviews = []
    unique_reviews = set()
    review_cards = soup.select('div.f6e3a11b0d.ae5dbab14d.e95943ce9b')

    for card in review_cards:
        if len(scraped_reviews) >= max_reviews:
            break
        positive_part = card.select_one('div[data-testid="review-positive-text"] div.b99b6ef58f span')
        negative_part = card.select_one('div[data-testid="review-negative-text"] div.b99b6ef58f span')
        review_parts = []
        if positive_part: review_parts.append(positive_part.get_text(strip=True))
        if negative_part: review_parts.append(negative_part.get_text(strip=True))
        full_review_text = " ".join(review_parts)
        if full_review_text and full_review_text not in unique_reviews:
            unique_reviews.add(full_review_text)
            scraped_reviews.append(full_review_text)
            
    return scraped_reviews

# --- 5. API Endpoints ---
@app.route('/predict', methods=['POST'])
def handle_prediction():
    if not request.json or 'review' not in request.json:
        return jsonify({'error': 'Invalid request.'}), 400
    review_text = request.json['review']
    prediction, score = predict_review(review_text)
    return jsonify({'prediction': prediction.upper(), 'authenticity_score': f"{score:.2f}"})

# UPDATED to use the new scraping function
@app.route('/scrape-and-predict', methods=['POST'])
def handle_scraping():
    if not request.json or 'url' not in request.json:
        return jsonify({'error': 'Invalid request. Please provide a "url" key.'}), 400
    
    target_url = request.json['url']
    try:
        scraped_reviews = scrape_with_api(target_url, max_reviews=50)
        
        if not scraped_reviews:
            return jsonify({'error': 'Could not scrape any reviews from the URL.'}), 404

        results = []
        for review_text in scraped_reviews:
            prediction, score = predict_review(review_text)
            results.append({
                'review_text': review_text[:100] + "...",
                'prediction': prediction.upper(),
                'authenticity_score': f"{score:.2f}"
            })
        
        print("Scraping and analysis complete.")
        return jsonify(results)
    except Exception as e:
        print(f"An error occurred during scraping/analysis: {e}")
        return jsonify({'error': 'An internal error occurred.'}), 500

# --- 6. Run the Flask App ---
if __name__ == '__main__':
    app.run(port=5000, debug=True)