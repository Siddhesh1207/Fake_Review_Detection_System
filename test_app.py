import requests
import json

# The URL of your running Flask API's predict endpoint
API_URL = "http://127.0.0.1:5000/predict"

# The review you want to test
review_text = "This product was the best I have ever used, truly amazing!"

# The data to send in the POST request (must be a dictionary)
payload = {"review": review_text}

try:
    # Send the POST request
    response = requests.post(API_URL, json=payload)
    response.raise_for_status()  # Raise an exception for bad status codes

    # Print the JSON response from the server
    print("Server Response:")
    print(response.json())

except requests.exceptions.RequestException as e:
    print(f"Error connecting to the API: {e}")