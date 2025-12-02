from flask import Flask, request, jsonify
from flask_cors import CORS 
import torch
import pandas as pd
from werkzeug.utils import secure_filename
import os
import torch.nn.functional as F
from transformers import RobertaTokenizer, RobertaForSequenceClassification, pipeline
from scraper import scrape_booking_reviews 
import re

app = Flask(__name__)
CORS(app) 

# --- MODEL 1: Your fine-tuned Fake/Real Classifier ---
MODEL_PATH = './final_model_distilroberta'
print("Loading the saved models and tokenizers...")
try:
    # Your existing model for fake vs. real prediction
    fake_review_tokenizer = RobertaTokenizer.from_pretrained(MODEL_PATH)
    fake_review_model = RobertaForSequenceClassification.from_pretrained(MODEL_PATH)
    fake_review_model.eval()

    # --- MODEL 2: Zero-Shot Model for Aspect & Sentiment Analysis ---
    print("Loading Zero-Shot classification pipeline...")
    zero_shot_classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
    
    print("All models loaded successfully!")
except Exception as e:
    print(f"Error loading models: {e}")
    exit()

LABELS = ['fake', 'real']

# --- ## FINAL, REFINED DUMMY DATABASE ## ---
existing_reviews_db = {
    "The Royal Pinnacle": [
        # Consensus: WiFi is EXCELLENT
        {"user": "Rohan", "review": "Blazing fast internet, I could stream 4K content without a single buffer. Perfect for my business needs."},
        {"user": "Priya", "review": "The connectivity here is top-notch. The WiFi signal was strong and stable in every corner of the hotel."},
        # Consensus: Room Service is TERRIBLE
        {"user": "Anjali", "review": "Called room service three times for a bottle of water and it took them over an hour to deliver. Very disappointing."},
        {"user": "Vikram", "review": "The room service staff were rude and my order arrived cold. A truly awful experience."},
        # Consensus: Food is EXCELLENT
        {"user": "Sunita", "review": "The breakfast buffet was the highlight of my stay. So many options and everything tasted delicious, especially the local dishes."},
        {"user": "Sameer", "review": "I had the best paneer tikka of my life at their restaurant. The chefs here are true artists."},
        # Consensus: Rooms are TERRIBLE
        {"user": "Fatima", "review": "Booked a 'deluxe' room which turned out to be tiny and cramped. The photos online are very misleading."},
        {"user": "David", "review": "The room felt old and worn out. The furniture was chipped and the bathroom had a strange smell."},
        # Consensus: Surroundings are EXCELLENT
        {"user": "Neha", "review": "Even though it's in a busy area, the hotel is surprisingly quiet and peaceful. The valet parking made everything so convenient."},
        {"user": "Kumar", "review": "The hotel is an oasis of calm. Secure and easy parking was a huge plus."}
    ],
    "Goa Shoreline Resort": [
        # Consensus: WiFi is TERRIBLE
        {"user": "Isabelle", "review": "Forget about getting any work done, the internet barely works in the rooms. Only usable in the lobby."},
        {"user": "John", "review": "The WiFi is a joke. It's slower than my 2G phone connection. Don't come here if you need to be online."},
        # Consensus: Room Service is EXCELLENT
        {"user": "Maria", "review": "Room service staff were so friendly and the late-night snacks menu was excellent. They went above and beyond."},
        {"user": "Leo", "review": "Lightning-fast room service! I ordered a meal at 1 AM and it arrived, hot and correct, in under 20 minutes."},
        # Consensus: Food is TERRIBLE
        {"user": "Chloe", "review": "The food is catered to foreign tourists with no spice. Very underwhelming for a place like Goa."},
        {"user": "Daniel", "review": "My fish curry was watery and tasteless. A complete disgrace to Goan cuisine."},
        # Consensus: Rooms are EXCELLENT
        {"user": "Sophie", "review": "Our sea-facing room was huge and spacious, with a beautiful balcony."},
        {"user": "Michael", "review": "The room was spotless, very large, and the bed was incredibly comfortable."},
        # Consensus: Surroundings are TERRIBLE
        {"user": "Olivia", "review": "It's located right next to a noisy shack that plays loud music until 2 AM. Not peaceful at all."},
        {"user": "Ben", "review": "The beach access is public and crowded, not private as advertised. The area feels a bit unsafe at night."}
    ],
    "Himalayan Serenity": [
        # Consensus: WiFi is EXCELLENT
        {"user": "Aarav", "review": "I was surprised to have such a stable and fast internet connection this high up in the mountains."},
        {"user": "Ishaan", "review": "The WiFi here is better than what I have at home in the city! Reliable and fast."},
        # Consensus: Room Service is TERRIBLE
        {"user": "Myra", "review": "Room service closes at 9 PM, which is far too early for a hotel. Very inconvenient for travelers."},
        {"user": "Kabir", "review": "It's clear they are understaffed. It took forever to get anyone to answer the room service line."},
        # Consensus: Food is EXCELLENT
        {"user": "Diya", "review": "The traditional Himachali food they served was authentic and incredibly flavorful. A must-try!"},
        {"user": "Arjun", "review": "The fresh mountain trout was cooked to perfection. Dining here was an absolute delight."},
        # Consensus: Rooms are TERRIBLE
        {"user": "Zara", "review": "The room was rustic, but that just meant it was old and poorly maintained. The heating was inadequate for the cold."},
        {"user": "Reyansh", "review": "Found insects in the bathroom and the linens didn't seem fresh. I was very uncomfortable during my stay."},
        # Consensus: Surroundings are EXCELLENT
        {"user": "Anika", "review": "The location is absolutely breathtaking and silent. Perfect for a peaceful retreat. Parking was easy to find."},
        {"user": "Vihaan", "review": "Waking up to the view of the snow-capped peaks from my window was a core memory. Incredibly peaceful."}
    ],
    "Jaipur Heritage Palace": [
        # Consensus: WiFi is TERRIBLE
        {"user": "William", "review": "The WiFi is non-existent. They claim to have it, but it just doesn't work. Had to use my mobile data the whole time."},
        {"user": "Emma", "review": "The thick palace walls seem to block all signals. Don't expect to have any functional internet here."},
        # Consensus: Room Service is EXCELLENT
        {"user": "James", "review": "Felt like royalty with their room service. The staff addressed me by name and were extremely attentive."},
        {"user": "Charlotte", "review": "Every request via room service was handled with grace and speed. Truly 5-star service."},
        # Consensus: Food is TERRIBLE
        {"user": "Henry", "review": "The food is incredibly expensive and not authentic at all. It's a classic tourist trap."},
        {"user": "Amelia", "review": "My meal was cold and the portions were tiny for the exorbitant price. A huge disappointment."},
        # Consensus: Rooms are EXCELLENT
        {"user": "George", "review": "Staying in the Maharaja suite was a dream. The room was gigantic, with beautiful traditional decor and artifacts."},
        {"user": "Ella", "review": "Our room was beautifully preserved and felt like stepping back in time, but with all modern comforts. Absolutely stunning."},
        # Consensus: Surroundings are TERRIBLE
        {"user": "Arthur", "review": "The constant noise from weddings and events held at the palace made it impossible to rest."},
        {"user": "Grace", "review": "The location is right on a busy, loud main road. The palace gardens are small and not well-maintained."}
    ],
    "Bangalore Tech Park Hotel": [
        # Consensus: WiFi is EXCELLENT
        {"user": "Advik", "review": "As expected for a hotel in the tech capital, the internet was flawless and incredibly high-speed."},
        {"user": "Saanvi", "review": "Gigabit speeds and zero downtime. This is the best hotel internet I've ever experienced, period."},
        # Consensus: Room Service is TERRIBLE
        {"user": "Ayaan", "review": "The service is robotic and impersonal. They just leave the tray and rush out without a word."},
        {"user": "Kiara", "review": "They completely forgot one of the items in my order and still tried to charge me for it."},
        # Consensus: Food is EXCELLENT
        {"user": "Vivaan", "review": "The international cuisine at the buffet is top-notch, catering to all palates. The sushi bar was a surprise hit!"},
        {"user": "Tara", "review": "The South Indian breakfast options were authentic and delicious. The filter coffee was perfect."},
        # Consensus: Rooms are TERRIBLE
        {"user": "Aditya", "review": "The room felt like a sterile, small box. It was clean but had absolutely no character or comfort."},
        {"user": "Ananya", "review": "For the price, the room is incredibly small. There's barely enough space to open a suitcase."},
        # Consensus: Surroundings are EXCELLENT
        {"user": "Ishaan", "review": "The location is perfect for business in the tech park, and the basement parking is secure and spacious."},
        {"user": "Riya", "review": "It's very well-connected to the metro and airport, making it an extremely convenient location for a business trip."}
    ]
}


ASPECT_LABELS = [
    'physical features of the guest room, including its size, bed comfort, and amenities', 
    'hotel staff, reception, and room service responsiveness', 
    'cleanliness of the room and hotel', 
    'WiFi speed, internet signal, and connectivity', 
    'quality and taste of restaurant food and breakfast', 
    'the hotel\'s geographical location, its surrounding environment, and parking facilities'
]
SENTIMENT_LABELS = ['positive feedback', 'negative feedback']

# --- Cache for storing consensus maps to improve performance and consistency ---
_consensus_cache = {}

# --- Helper function to split reviews ---
def split_review_into_clauses(review_text):
    """Splits a review by conjunctions and punctuation to analyze parts separately."""
    clauses = re.split(r'\s*[,.]\s*|\s+\b(?:but|and)\b\s+', review_text)
    return [clause.strip() for clause in clauses if clause and clause.strip()]


# --- Helper function using the transformer pipeline ---
def analyze_review_aspect_and_sentiment(review_text):
    """
    Uses a zero-shot classification model to determine the primary aspect and sentiment of a review.
    """
    aspect_result = zero_shot_classifier(review_text, candidate_labels=ASPECT_LABELS)
    top_aspect = aspect_result['labels'][0]
    sentiment_result = zero_shot_classifier(review_text, candidate_labels=SENTIMENT_LABELS)
    top_sentiment = sentiment_result['labels'][0]
    return top_aspect, top_sentiment

# --- Your existing prediction function (no changes) ---
def predict_review(review_text):
    inputs = fake_review_tokenizer(review_text, return_tensors="pt", padding=True, truncation=True, max_length=256)
    with torch.no_grad():
        outputs = fake_review_model(**inputs)
    logits = outputs.logits
    probabilities = F.softmax(logits, dim=1)
    prediction_index = torch.argmax(probabilities, dim=1).item()
    predicted_label = LABELS[prediction_index]
    confidence_score = probabilities[0][prediction_index].item() * 100 
    return predicted_label, confidence_score


# --- API Endpoint now uses caching ---
@app.route('/cross-check-review', methods=['POST'])
def handle_cross_check():
    data = request.get_json()
    if not data or 'hotel_name' not in data or 'review_text' not in data:
        return jsonify({'error': 'Request must include "hotel_name" and "review_text"'}), 400

    hotel_name = data['hotel_name']
    new_review_text = data['review_text']

    if hotel_name not in existing_reviews_db:
        return jsonify({'verdict': 'INCONCLUSIVE', 'reason': f'Not enough data for "{hotel_name}" to perform a cross-check.'}), 200

    # --- CACHING LOGIC ---
    if hotel_name in _consensus_cache:
        consensus_map = _consensus_cache[hotel_name]
    else:
        print(f"--- Building new consensus cache for {hotel_name} ---")
        consensus_map = {}
        for review in existing_reviews_db[hotel_name]:
            aspect, sentiment = analyze_review_aspect_and_sentiment(review['review'])
            if aspect not in consensus_map:
                consensus_map[aspect] = []
            consensus_map[aspect].append(sentiment)
        _consensus_cache[hotel_name] = consensus_map
        print(f"--- Cache for {hotel_name} built: {consensus_map} ---")
    # --- END CACHING LOGIC ---

    clauses = split_review_into_clauses(new_review_text)
    if not clauses:
        return jsonify({'verdict': 'INCONCLUSIVE', 'reason': 'Review text is too short to analyze.'}), 200

    analysis_results = []
    is_outlier_found = False

    for clause in clauses:
        clause_aspect, clause_sentiment = analyze_review_aspect_and_sentiment(clause)

        if clause_aspect in consensus_map:
            sentiments = consensus_map[clause_aspect]
            positive_count = sentiments.count('positive feedback')
            negative_count = len(sentiments) - positive_count
            
            is_clause_outlier = False
            reason = ""
            
            if clause_sentiment == 'positive feedback' and negative_count > positive_count:
                is_clause_outlier = True
                is_outlier_found = True
                reason = f"This positive comment conflicts with a mostly negative consensus ({negative_count} vs {positive_count}) on this topic."
            
            elif clause_sentiment == 'negative feedback' and positive_count > negative_count:
                is_clause_outlier = True
                is_outlier_found = True
                reason = f"This negative comment conflicts with a mostly positive consensus ({positive_count} vs {negative_count}) on this topic."
            
            else:
                reason = "This comment is consistent with feedback from other guests."
            
            analysis_results.append({
                "clause": clause,
                "aspect": clause_aspect,
                "sentiment": clause_sentiment.split(' ')[0],
                "is_outlier": is_clause_outlier,
                "reason": reason
            })
        else:
             analysis_results.append({
                "clause": clause,
                "aspect": clause_aspect,
                "sentiment": clause_sentiment.split(' ')[0],
                "is_outlier": False,
                "reason": "There is not enough historical data about this specific topic to form a consensus."
            })


    if not analysis_results:
        return jsonify({'verdict': 'INCONCLUSIVE', 'reason': 'Could not identify specific aspects in the review.'}), 200

    if is_outlier_found:
        overall_verdict = "FAKE_REVIEW"
    else:
        overall_verdict = "GENUINE_REVIEW"
        
    return jsonify({
        "overall_verdict": overall_verdict,
        "analysis": analysis_results
    })


# --- Existing API Endpoints 
@app.route('/predict', methods=['POST'])
def handle_prediction():
    if not request.json or 'review' not in request.json:
        return jsonify({'error': 'Invalid request. Please provide a JSON with a "review" key.'}), 400
    review_text = request.json['review']
    try:
        prediction, confidence_score = predict_review(review_text)
        response_data = {
            'prediction': prediction.upper(),
            'confidence_score': f"{confidence_score:.2f}%"
        }
        return jsonify(response_data)
    except Exception as e:
        print(f"Error during prediction: {e}")
        return jsonify({'error': 'Failed to process the review.'}), 500
    
@app.route('/scrape-and-predict', methods=['POST'])
def handle_scraping():
    if not request.json or 'url' not in request.json:
        return jsonify({'error': 'Invalid request. Please provide a "url" key.'}), 400
    target_url = request.json['url']
    try:
        reviews_df = scrape_booking_reviews(target_url, max_reviews=50)
        if reviews_df.empty:
            return jsonify({'error': 'Could not scrape any reviews from the URL.'}), 404
        results = []
        for review_text in reviews_df['review']:
            prediction, confidence_score = predict_review(review_text)
            results.append({
                'review_text': review_text[:100] + "...",
                'prediction': prediction.upper(),
                'confidence_score': f"{confidence_score:.2f}%"
            })
        print("Scraping and analysis complete.")
        return jsonify(results)
    except Exception as e:
        print(f"An error occurred during scraping/analysis: {e}")
        return jsonify({'error': 'An internal error occurred.'}), 500

@app.route('/analyze-file', methods=['POST'])
def analyze_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'File must be a CSV'}), 400
    try:
        df = pd.read_csv(file)
        if 'review' not in df.columns:
            return jsonify({'error': 'CSV must contain a "review" column'}), 400
        results = []
        for review in df['review'].fillna(''):
            if isinstance(review, str) and review.strip():
                prediction, confidence_score = predict_review(review)
                results.append({
                    'review': review,
                    'prediction': prediction.upper(),
                    'confidence_score': f"{confidence_score:.2f}%"
                })
        return jsonify(results)
    except Exception as e:
        print(f"Error processing file: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860)

